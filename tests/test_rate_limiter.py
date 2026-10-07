"""Unit tests for Redis sliding-window decision handling."""

import hashlib

import pytest
from fastapi import HTTPException

from app.core.rate_limiter import RedisSlidingWindowRateLimiter


class FakeRedis:
    """Capture the atomic script invocation and return a configured decision."""

    def __init__(self, result: list[int] | None = None, error: Exception | None = None) -> None:
        self.result = result or [1, 0, 4]
        self.error = error
        self.eval_args = None

    async def eval(self, *args):
        self.eval_args = args
        if self.error is not None:
            raise self.error
        return self.result


@pytest.mark.anyio
async def test_rate_limiter_returns_allowed_decision_and_hashes_identity() -> None:
    redis = FakeRedis([1, 0, 4])
    limiter = RedisSlidingWindowRateLimiter(redis, limit=5, window_seconds=30)

    result = await limiter.check("192.0.2.15")

    assert result.allowed is True
    assert result.limit == 5
    assert result.remaining == 4
    assert redis.eval_args[1] == 1
    assert redis.eval_args[2] == (
        "inference:rate-limit:" + hashlib.sha256(b"192.0.2.15").hexdigest()
    )
    assert redis.eval_args[3:5] == (30000, 5)


@pytest.mark.anyio
async def test_rate_limiter_returns_retry_delay_when_window_is_full() -> None:
    limiter = RedisSlidingWindowRateLimiter(FakeRedis([0, 22501, 0]), limit=2)

    decision = await limiter.check("client-a")

    assert decision.allowed is False
    assert decision.remaining == 0
    assert decision.retry_after == 23


@pytest.mark.anyio
async def test_rate_limiter_fails_closed_when_redis_is_unavailable() -> None:
    limiter = RedisSlidingWindowRateLimiter(FakeRedis(error=ConnectionError("offline")))

    with pytest.raises(HTTPException) as raised:
        await limiter.check("client-a")

    assert raised.value.status_code == 503
    assert raised.value.headers == {"Retry-After": "1"}


@pytest.mark.parametrize(
    ("limit", "window_seconds"),
    [(0, 60), (10, 0)],
)
def test_rate_limiter_rejects_non_positive_configuration(
    limit: int,
    window_seconds: int,
) -> None:
    with pytest.raises(ValueError):
        RedisSlidingWindowRateLimiter(FakeRedis(), limit, window_seconds)