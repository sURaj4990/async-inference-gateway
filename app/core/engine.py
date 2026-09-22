from typing import AsyncGenerator
import ollama
from app.schemas.inference import GenerationRequest, StreamChunk