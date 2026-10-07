"""Redis-backed, per-client sliding-window limits for inference requests."""

import hashlib
import math
import uuid
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis


SLIDING_WINDOW_SCRIPT = """
local now = redis.call('TIME')
local now_ms = (now[1] * 1000) + math.floor(now[2] / 1000)
local window_ms = tonumber(ARGV[1])
local request_limit = tonumber(ARGV[2])
local cutoff = now_ms - window_ms

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff)
local count = redis.call('ZCARD', KEYS[1])
if count >= request_limit then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    local retry_after_ms = math.max(1, tonumber(oldest[2]) + window_ms - now_ms)
    return {0, retry_after_ms, 0}
end

redis.call('ZADD', KEYS[1], now_ms, ARGV[3])
redis.call('PEXPIRE', KEYS[1], window_ms)
return {1, 0, request_limit - count - 1}
"""


@dataclass(frozen=True)
class RateLimitDecision:
    """Outcome and response metadata from one rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int = 0


class RedisSlidingWindowRateLimiter:
    """Atomically cap request starts per identity over a rolling time window."""

    def __init__(self, redis: Redis, limit: int = 10, window_seconds: int = 60) -> None:
        if limit < 1:
            raise ValueError("Rate limit must be at least 1 request")
        if window_seconds < 1:
            raise ValueError("Rate-limit window must be at least 1 second")

        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    async def check(self, identity: str) -> RateLimitDecision:
        """Consume one request slot or raise 503 if Redis cannot enforce policy."""
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        key = f"inference:rate-limit:{identity_hash}"
        try:
            allowed, retry_after_ms, remaining = await self.redis.eval(
                SLIDING_WINDOW_SCRIPT,
                1,
                key,
                self.window_seconds * 1000,
                self.limit,
                uuid.uuid4().hex,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate-limit service is unavailable",
                headers={"Retry-After": "1"},
            ) from exc

        return RateLimitDecision(
            allowed=bool(allowed),
            limit=self.limit,
            remaining=int(remaining),
            retry_after=math.ceil(int(retry_after_ms) / 1000),
        )


async def enforce_inference_rate_limit(request: Request) -> None:
    """Apply the shared IP-based limit before an inference response streams."""
    client_host = request.client.host if request.client is not None else "unknown"
    decision = await request.app.state.rate_limiter.check(client_host)
    headers = {
        "X-RateLimit-Limit": str(decision.limit),
        "X-RateLimit-Remaining": str(decision.remaining),
    }

    if not decision.allowed:
        headers["Retry-After"] = str(decision.retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Inference request rate limit exceeded",
            headers=headers,
        )

    request.state.rate_limit_headers = headers