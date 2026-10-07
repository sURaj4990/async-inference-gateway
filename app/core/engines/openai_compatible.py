"""Streaming adapter for OpenAI-compatible chat completion APIs."""

from typing import AsyncGenerator
from openai import AsyncOpenAI
from app.schemas.inference import OpenAIRequest, StreamChunk
from app.core.engines.base import BaseInferenceEngine

class OpenAIEngine(BaseInferenceEngine):
    """Forward chat prompts and normalize streamed completion deltas."""

    async def stream_generate(self, req: OpenAIRequest) -> AsyncGenerator[StreamChunk, None]:
        """Yield each non-empty content delta and close the API client."""
        client = AsyncOpenAI(
            base_url=req.base_url,
            api_key=req.api_key
        )
        try:
            response = await client.chat.completions.create(
                model=req.model,
                messages=[{
                    "role": "user",
                    "content": req.prompt, 
                }],
                temperature=req.temperature,
                stream=True
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield StreamChunk(token=content, is_finished=False)
            yield StreamChunk(token="", is_finished=True)   
        
        except Exception as e:
            yield StreamChunk(token="", is_finished=True, error=str(e))

        finally:
            await client.close()