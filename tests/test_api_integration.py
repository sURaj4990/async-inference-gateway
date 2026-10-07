"""In-process integration tests for the versioned streaming API."""

import json
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes import router
from app.core.rate_limiter import RateLimitDecision
from app.schemas.inference import StreamChunk


class FakeEngine:
    """Small engine substitute that records validated request models."""

    def __init__(self) -> None:
        self.requests = []

    async def stream_generate(self, req) -> AsyncGenerator[StreamChunk, None]:
        self.requests.append(req)
        yield StreamChunk(token="test ")
        yield StreamChunk(token="reply", is_finished=False)
        yield StreamChunk(token="", is_finished=True)


class FakeRateLimiter:
    """Deterministic limiter substitute for route behavior tests."""

    def __init__(self) -> None:
        self.decision = RateLimitDecision(allowed=True, limit=10, remaining=9)
        self.identities = []

    async def check(self, identity: str) -> RateLimitDecision:
        self.identities.append(identity)
        return self.decision


@pytest.fixture
def client_and_engines() -> tuple[TestClient, dict[str, FakeEngine], FakeRateLimiter]:
    app = FastAPI()
    app.include_router(router)
    engines = {
        "local": FakeEngine(),
        "ollama": FakeEngine(),
        "openai": FakeEngine(),
    }
    app.state.hf_engine = engines["local"]
    app.state.ollama_engine = engines["ollama"]
    app.state.openai_engine = engines["openai"]
    limiter = FakeRateLimiter()
    app.state.rate_limiter = limiter
    return TestClient(app), engines, limiter


@pytest.mark.parametrize(
    ("path", "payload", "engine_name"),
    [
        (
            "/v1/chat/stream/local",
            {"prompt": "hello", "max_new_tokens": 24, "temperature": 0.2},
            "local",
        ),
        (
            "/v1/chat/stream/ollama",
            {"model": "qwen2", "prompt": "hello", "temperature": 0.2},
            "ollama",
        ),
        (
            "/v1/chat/stream/openai",
            {
                "base_url": "https://example.test/v1",
                "api_key": "test-key",
                "model": "test-model",
                "prompt": "hello",
                "temperature": 0.2,
            },
            "openai",
        ),
    ],
)
def test_inference_route_streams_chunks_and_dispatches_request(
    client_and_engines: tuple[TestClient, dict[str, FakeEngine], FakeRateLimiter],
    path: str,
    payload: dict,
    engine_name: str,
) -> None:
    client, engines, limiter = client_and_engines

    response = client.post(path, json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-ratelimit-limit"] == "10"
    assert response.headers["x-ratelimit-remaining"] == "9"
    chunks = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert chunks == [
        {"token": "test ", "is_finished": False, "error": None},
        {"token": "reply", "is_finished": False, "error": None},
        {"token": "", "is_finished": True, "error": None},
    ]
    assert len(engines[engine_name].requests) == 1
    assert engines[engine_name].requests[0].prompt == "hello"
    assert limiter.identities == ["testclient"]


def test_inference_route_rejects_invalid_request(
    client_and_engines: tuple[TestClient, dict[str, FakeEngine], FakeRateLimiter],
) -> None:
    client, _, _ = client_and_engines

    response = client.post(
        "/v1/chat/stream/local",
        json={"prompt": "hello", "max_new_tokens": 0},
    )

    assert response.status_code == 422


def test_inference_route_rejects_requests_over_the_rate_limit(
    client_and_engines: tuple[TestClient, dict[str, FakeEngine], FakeRateLimiter],
) -> None:
    client, engines, limiter = client_and_engines
    limiter.decision = RateLimitDecision(
        allowed=False,
        limit=10,
        remaining=0,
        retry_after=23,
    )

    response = client.post(
        "/v1/chat/stream/local",
        json={"prompt": "hello"},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Inference request rate limit exceeded"
    assert response.headers["retry-after"] == "23"
    assert response.headers["x-ratelimit-remaining"] == "0"
    assert engines["local"].requests == []
