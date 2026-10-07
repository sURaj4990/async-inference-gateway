import json
from typing import AsyncGenerator
import httpx

from app.core.engines.base import BaseInferenceEngine
from app.schemas.inference import OllamaRequest, StreamChunk

class OllamaEngine(BaseInferenceEngine):
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")
        
    async def stream_generate(self, req: OllamaRequest) -> AsyncGenerator[StreamChunk, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": req.model,
            "prompt": req.prompt,
            "options": {
                "temperature": req.temperature
            },
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        token = data.get("response", "")
                        is_done = data.get("done", False)
                        yield StreamChunk(token=token, is_finished=is_done)

                    yield StreamChunk(token="", is_finished=True)

        except Exception as e:
            yield StreamChunk(token="", is_finished=True, error=str(e))
                    

