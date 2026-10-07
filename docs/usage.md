# Usage and Configuration

## Local development

Install runtime, UI, and development dependencies with uv:

```powershell
uv sync --extra ui --group dev
```

Run the API and interface in separate terminals:

```powershell
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app.py
```

The Streamlit sidebar defaults to `http://localhost:8000`. Set `INFERENCE_API_URL` to point the UI at another gateway instance:

```powershell
$env:INFERENCE_API_URL = "http://localhost:8000"
uv run streamlit run streamlit_app.py
```

For local Ollama use, start Ollama on the same host and pull the selected model, for example `ollama pull llama3`. For the OpenAI-compatible provider, enter a reachable API base URL, model name, and API key in the sidebar. The key is sent from the UI to FastAPI in the request body and is not stored by this interface.

## Docker Compose

Build and start all services:

```powershell
docker compose up --build
```

The UI is exposed on port 8501, the API on port 8000, and Ollama on port 11434. The API's startup loads the Hugging Face model and can take a while on first boot. Docker volumes preserve Hugging Face and Ollama caches across restarts.

Compose also starts Redis with a persistent data volume. The API waits for Redis health before starting. By default, each client IP may start 10 inference requests in a rolling 60-second window across all three providers. Override `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` in the API service environment to change this policy. Redis connectivity is required: if it becomes unavailable, inference requests receive `503` until it recovers.

Download an Ollama model after the service is up:

```powershell
docker compose exec ollama ollama pull llama3
```

To inspect startup and model-loading logs:

```powershell
docker compose logs -f api
```

Stop the services while preserving downloaded model data:

```powershell
docker compose down
```

Removing volumes with `docker compose down --volumes` also deletes the downloaded model caches.

## API exploration

FastAPI's OpenAPI UI is available at `/docs` on the API host. Check readiness with `GET /health`. The inference requests are POST requests and return a streaming SSE response rather than a JSON document.

## Configuration boundaries

The current application fixes the Hugging Face model ID in `app/main.py` and the Ollama URL in its engine adapter. Changing either requires a code change. The Streamlit gateway URL can be selected in the sidebar or provided with `INFERENCE_API_URL`. Keep the API private or put it behind an authenticated reverse proxy before exposing it to untrusted networks.
