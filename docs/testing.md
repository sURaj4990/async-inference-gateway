# Testing

## Run the suite

Install the development group and run pytest:

```powershell
uv sync --extra ui --group dev
uv run pytest -q
```

## Coverage

- `tests/test_streamlit_client.py` checks provider URL selection, payload shape, token decoding, stream completion, and surfaced engine errors.
- `tests/test_api_integration.py` exercises each FastAPI route through an in-process ASGI test client, checks emitted SSE chunks, and verifies schema validation responses.
- `tests/test_inference_schemas.py` checks valid request defaults and numeric boundaries.

The route integration tests construct a small FastAPI app with fake engines instead of importing the production lifespan. This keeps tests deterministic, offline, and independent of Hugging Face downloads, Ollama, and remote API credentials.

When adding a provider, cover its request schema, provider-specific payload construction in the Streamlit client, route dispatch, and the final/error stream-chunk behavior.
