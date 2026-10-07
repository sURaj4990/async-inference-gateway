from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.v1.utils import format_sse_stream
from app.schemas.inference import LocalHFRequest, OllamaRequest, OpenAIRequest

router = APIRouter(prefix="/v1/chat/stream", tags=["Inference"])

@router.post("/local")
async def stream_local_hf(req: LocalHFRequest, request: Request):
    hf_engine = request.app.state.hf_engine
    stream = hf_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream"
    )

@router.post("/ollama")
async def stream_ollama(req: OllamaRequest, request: Request):
    ollama_engine = request.app.state.ollama_engine
    stream = ollama_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream"
    )

@router.post("/openai")
async def stream_openai_like(req: OpenAIRequest, request: Request):
    openai_engine = request.app.state.openai_engine
    stream = openai_engine.stream_generate(req)
    return StreamingResponse(
        format_sse_stream(stream),
        media_type="text/event-stream"
    )