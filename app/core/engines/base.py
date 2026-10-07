from abc import ABC, abstractmethod 
from typing import AsyncGenerator
from app.schemas.inference import StreamChunk

# ABC - Abstract Base Class
class BaseInferenceEngine(ABC):
    @abstractmethod
    async def stream_generate(self, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """ 
        Yields standardized StreamChunk items asynchronously.
        Must yield at least one chunk with is_finished=True before terminating.
        """
        pass