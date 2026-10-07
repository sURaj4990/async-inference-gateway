from typing import AsyncGenerator
from app.schemas.inference import StreamChunk

async def format_sse_stream(engine_stream: AsyncGenerator[StreamChunk, None]) -> AsyncGenerator[str, None]:
    async for chunk in engine_stream:
        yield f"data: {chunk.model_dump_json()}\n\n"