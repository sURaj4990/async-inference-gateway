"""FastAPI application entry point and model-engine lifecycle."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from redis.asyncio import Redis

from app.api.v1.routes import router
from app.core.engines.huggingface import HuggingFaceEngine
from app.core.engines.ollama import OllamaEngine
from app.core.engines.openai_compatible import OpenAIEngine
from app.core.rate_limiter import RedisSlidingWindowRateLimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect shared services, initialize engines, and release resources."""
    print("\n--- Starting Gateway: Initializing Engine ---")

    redis_client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    try:
        await redis_client.ping()
        app.state.rate_limiter = RedisSlidingWindowRateLimiter(
            redis=redis_client,
            limit=int(os.getenv("RATE_LIMIT_REQUESTS", "10")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        )
        app.state.ollama_engine = OllamaEngine()
        app.state.openai_engine = OpenAIEngine()
        # Loading here keeps model initialization out of individual request handlers.
        app.state.hf_engine = HuggingFaceEngine(model_id="Qwen/Qwen2.5-0.5B-Instruct")
        app.state.hf_engine.load_model()

        print("--- All Engines are Ready to Serve the Traffic ---\n")
        yield
    finally:
        await redis_client.aclose()
        print("\n--- Shutting Down Gateway ---")

app = FastAPI(title="Modular Inference Gateway", lifespan=lifespan)
app.include_router(router=router)

@app.get("/health", status_code=200, tags=['Health'])
def health_check() -> dict:
    """Return a lightweight liveness response for probes and operators."""
    return {
        "status": "healthy",
        "message": "applicaion is running"
    }