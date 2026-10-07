"""Unit tests for inference request model defaults and validation limits."""

import pytest
from pydantic import ValidationError

from app.schemas.inference import LocalHFRequest, OllamaRequest, OpenAIRequest


def test_request_models_apply_documented_defaults() -> None:
    assert LocalHFRequest(prompt="hello").model_dump() == {
        "prompt": "hello",
        "max_new_tokens": 128,
        "temperature": 0.7,
    }
    assert OllamaRequest(prompt="hello").model == "llama3"


@pytest.mark.parametrize("temperature", [-0.01, 2.01])
def test_request_models_reject_temperature_outside_range(temperature: float) -> None:
    with pytest.raises(ValidationError):
        OllamaRequest(prompt="hello", temperature=temperature)


def test_openai_request_requires_credentials_and_model() -> None:
    with pytest.raises(ValidationError):
        OpenAIRequest(prompt="hello")
