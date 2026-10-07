"""Versioned HTTP routes for streaming inference requests."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.v1.utils import format_sse_stream
from app.core.rate_limiter import enforce_inference_rate_limit
from app.schemas.inference import LocalHFRequest, OllamaRequest, OpenAIRequest

router = APIRouter(
    prefix="/v1/chat/stream",
    tags=["Inference"],
    dependencies=[Depends(enforce_inference_rate_limit)],
)

@router.post("/local")
async def stream_local_hf(req: LocalHFRequest, request: Request):
    """Stream output from the Hugging Face engine initialized at startup."""
    hf_engine = request.app.state.hf_engine
    stream = hf_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream",
        headers=request.state.rate_limit_headers,
    )

@router.post("/ollama")
async def stream_ollama(req: OllamaRequest, request: Request):
    """Stream output from the configured Ollama server."""
    ollama_engine = request.app.state.ollama_engine
    stream = ollama_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream",
        headers=request.state.rate_limit_headers,
    )

@router.post("/openai")
async def stream_openai_like(req: OpenAIRequest, request: Request):
    """Stream output from an OpenAI-compatible chat completions endpoint."""
    openai_engine = request.app.state.openai_engine
    stream = openai_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream",
        headers=request.state.rate_limit_headers,
    )