# Architecture and API

## Components

The application has three layers:

1. `app/api/v1/routes.py` exposes the versioned streaming endpoints.
2. `app/core/engines/` adapts Hugging Face, Ollama, and OpenAI-compatible streaming into a shared `StreamChunk` schema.
3. `streamlit_app.py` sends requests to the gateway and renders each received token as it arrives.

FastAPI initializes the Ollama and OpenAI-compatible adapters at startup and eagerly loads the default Hugging Face model. The Hugging Face download therefore occurs before the API reports ready. Model cache storage should be persistent in container deployments.

## Endpoints

| Method | Path | Backend |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/v1/chat/stream/local` | Local Hugging Face model |
| `POST` | `/v1/chat/stream/ollama` | Ollama HTTP API |
| `POST` | `/v1/chat/stream/openai` | OpenAI-compatible chat completions API |

The inference routes respond with `text/event-stream`. Each SSE `data:` line contains a JSON `StreamChunk` with `token`, `is_finished`, and optional `error` fields. Clients should concatenate token values until `is_finished` is true and handle a non-empty `error` as a failed generation.

Before an inference stream starts, a Redis-backed sliding-window limiter checks the caller's client IP across all three providers. The default is 10 request starts per 60 seconds. Successful responses include `X-RateLimit-Limit` and `X-RateLimit-Remaining`; rejected requests return `429` with `Retry-After`. If Redis cannot enforce the policy, the API returns `503` rather than allowing unmetered inference. The health endpoint is not rate limited.

### Request bodies

Local Hugging Face:

```json
{"prompt":"Explain async IO","max_new_tokens":128,"temperature":0.7}
```

Ollama:

```json
{"model":"llama3","prompt":"Explain async IO","temperature":0.7}
```

OpenAI-compatible:

```json
{"base_url":"https://api.openai.com/v1","api_key":"<secret>","model":"gpt-4o-mini","prompt":"Explain async IO","temperature":0.7}
```

The OpenAI-compatible `base_url` must be reachable from the FastAPI process. Within Compose, use a network-reachable service URL for a separately hosted provider, not a URL that only resolves from the browser.

## Provider behavior

- The Hugging Face model is fixed by the FastAPI lifespan to `Qwen/Qwen2.5-0.5B-Instruct`; its request supports `max_new_tokens` from 1 through 512 and temperature from 0 through 2.
- Ollama's adapter targets `http://localhost:11434`. Compose shares the API container's network namespace with the Ollama service so that this existing default continues to resolve.
- OpenAI-compatible calls use the supplied base URL, API key, and model name. They work with any compatible endpoint reachable from the API container.

## Operational considerations

The API currently has no authentication or authorization. IP-based limits identify callers by the connection peer; behind a proxy, configure the proxy and server trust boundary carefully before relying on client IPs. When requests pass through the Streamlit service in Compose, they share the Streamlit container's quota. All providers share one quota per IP, and concurrent active streams are not limited separately. The local Hugging Face model is loaded into CPU memory using float32 weights, so provision adequate RAM and persistent model-cache storage. The API streams provider errors as final stream chunks; clients should inspect the `error` property even when the HTTP response status is successful.
