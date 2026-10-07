"""Shared asynchronous interface implemented by all inference adapters."""

from abc import ABC, abstractmethod 
from typing import AsyncGenerator
from app.schemas.inference import StreamChunk

# ABC - Abstract Base Class
class BaseInferenceEngine(ABC):
    """Contract for engines that yield normalized streaming response chunks."""
    @abstractmethod
    async def stream_generate(self, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """ 
        Yields standardized StreamChunk items asynchronously.
        Must yield at least one chunk with is_finished=True before terminating.
        """
        pass