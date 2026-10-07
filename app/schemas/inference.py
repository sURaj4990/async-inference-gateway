from typing import Optional
from pydantic import BaseModel, Field

class StreamChunk(BaseModel):
    token: str
    is_finished: bool = False
    error: Optional[str] = None

class LocalHFRequest(BaseModel):
    prompt: str = Field()
    max_new_tokens: int = Field(default=128, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class OllamaRequest(BaseModel):
    model: str = Field(default="llama3")
    prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class OpenAIRequest(BaseModel):
    base_url: str = Field(default="https://api.openai.com/v1")
    api_key: str
    model: str
    prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)