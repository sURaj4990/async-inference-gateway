"""Utilities for converting engine output to HTTP streaming formats."""

from typing import AsyncGenerator
from app.schemas.inference import StreamChunk

async def format_sse_stream(engine_stream: AsyncGenerator[StreamChunk, None]) -> AsyncGenerator[str, None]:
    """Encode each standardized engine chunk as a server-sent event."""
    async for chunk in engine_stream:
        yield f"data: {chunk.model_dump_json()}\n\n"