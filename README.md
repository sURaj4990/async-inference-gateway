# Modular Inference Gateway

A FastAPI service that streams generated text from local Hugging Face models, Ollama, and OpenAI-compatible APIs. A minimal Streamlit chat client is included for interactive use.

## Quick Start

Requirements: Python 3.13+, [uv](https://docs.astral.sh/uv/), and an available model backend. Hugging Face model weights are loaded when the API starts; the default is `Qwen/Qwen2.5-0.5B-Instruct`.

```powershell
uv sync --extra ui --group dev
uv run uvicorn app.main:app --reload
```

In a second terminal, start the UI:

```powershell
uv run streamlit run streamlit_app.py
```

Open <http://localhost:8501>. The API health endpoint is <http://localhost:8000/health>, and the interactive API reference is at <http://localhost:8000/docs>.

## Docker Compose

Compose starts the API, Streamlit, and Ollama. The first API start downloads the Hugging Face model and may take several minutes.

```powershell
docker compose up --build
```

Open <http://localhost:8501>. Before using the Ollama provider, pull a model:

```powershell
docker compose exec ollama ollama pull llama3
```

See [the documentation](docs/README.md) for API schemas, provider setup, architecture, testing, and deployment notes.

## Tests

```powershell
uv run --group dev pytest -q
```

Tests use fake inference engines and do not download model weights or contact external model providers.

Inference endpoints use Redis to enforce a configurable per-IP sliding-window request limit (10 requests per 60 seconds by default). See [usage and configuration](docs/usage.md) for deployment details.
