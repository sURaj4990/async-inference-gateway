"""Unit tests for Streamlit request construction and SSE decoding."""

import json

import pytest

from streamlit_app import build_payload, endpoint_url, stream_response


@pytest.mark.parametrize(
    ("provider", "path"),
    [
        ("Local Hugging Face", "/local"),
        ("Ollama", "/ollama"),
        ("OpenAI-compatible API", "/openai"),
    ],
)
def test_endpoint_url_selects_provider_route(provider: str, path: str) -> None:
    assert endpoint_url("http://gateway:8000/", provider) == (
        f"http://gateway:8000/v1/chat/stream{path}"
    )


def test_endpoint_url_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported provider"):
        endpoint_url("http://gateway:8000", "unknown")


def test_build_payload_matches_local_hugging_face_schema() -> None:
    payload = build_payload(
        "Local Hugging Face", "hello", 0.4, "ignored", 64, "ignored", "ignored"
    )
    assert payload == {"prompt": "hello", "temperature": 0.4, "max_new_tokens": 64}


def test_build_payload_matches_ollama_schema() -> None:
    payload = build_payload("Ollama", "hello", 0.4, "qwen2", 64, "ignored", "ignored")
    assert payload == {"prompt": "hello", "temperature": 0.4, "model": "qwen2"}


def test_build_payload_matches_openai_compatible_schema() -> None:
    payload = build_payload(
        "OpenAI-compatible API",
        "hello",
        0.4,
        "gpt-test",
        64,
        "https://example.test/v1",
        "secret",
    )
    assert payload == {
        "prompt": "hello",
        "temperature": 0.4,
        "base_url": "https://example.test/v1",
        "api_key": "secret",
        "model": "gpt-test",
    }


def test_stream_response_yields_tokens_until_finished(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_lines(self):
            events = [
                {"token": "Hello", "is_finished": False},
                {"token": " world", "is_finished": False},
                {"token": "", "is_finished": True},
                {"token": "ignored", "is_finished": False},
            ]
            return (f"data: {json.dumps(event)}" for event in events)

    monkeypatch.setattr("streamlit_app.httpx.stream", lambda *_args, **_kwargs: FakeResponse())
    assert list(stream_response("http://gateway", "Ollama", {})) == ["Hello", " world"]


def test_stream_response_surfaces_engine_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_lines(self):
            return iter(['data: {"token":"","is_finished":true,"error":"offline"}'])

    monkeypatch.setattr("streamlit_app.httpx.stream", lambda *_args, **_kwargs: FakeResponse())
    with pytest.raises(RuntimeError, match="offline"):
        list(stream_response("http://gateway", "Ollama", {}))