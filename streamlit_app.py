"""Minimal chat interface for the inference gateway's streaming endpoints."""

import json
import os
from collections.abc import Iterator
from typing import Any

import httpx
import streamlit as st


PROVIDER_PATHS = {
    "Local Hugging Face": "/local",
    "Ollama": "/ollama",
    "OpenAI-compatible API": "/openai",
}


def endpoint_url(api_base_url: str, provider: str) -> str:
    """Build the chat endpoint URL for a configured provider."""
    try:
        provider_path = PROVIDER_PATHS[provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider}") from exc
    return f"{api_base_url.rstrip('/')}/v1/chat/stream{provider_path}"


def build_payload(
    provider: str,
    prompt: str,
    temperature: float,
    model: str,
    max_new_tokens: int,
    base_url: str,
    api_key: str,
) -> dict[str, Any]:
    """Create the provider-specific body expected by the FastAPI schema."""
    payload: dict[str, Any] = {"prompt": prompt, "temperature": temperature}

    if provider == "Local Hugging Face":
        payload["max_new_tokens"] = max_new_tokens
    elif provider == "Ollama":
        payload["model"] = model
    elif provider == "OpenAI-compatible API":
        payload.update({"base_url": base_url, "api_key": api_key, "model": model})
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return payload


def stream_response(
    api_base_url: str,
    provider: str,
    payload: dict[str, Any],
) -> Iterator[str]:
    """Yield token text from the gateway's JSON-encoded SSE stream."""
    with httpx.stream(
        "POST",
        endpoint_url(api_base_url, provider),
        json=payload,
        timeout=180.0,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue

            event = json.loads(line.removeprefix("data:").strip())
            if event.get("error"):
                raise RuntimeError(event["error"])
            if event.get("token"):
                yield event["token"]
            if event.get("is_finished"):
                break


def main() -> None:
    """Render the chat UI and stream replies from the selected engine."""
    st.set_page_config(page_title="Inference Gateway", page_icon="💬")
    st.title("Inference Gateway")

    with st.sidebar:
        st.subheader("Connection")
        api_base_url = st.text_input(
            "Gateway URL",
            value=os.getenv("INFERENCE_API_URL", "http://localhost:8000"),
        )
        provider = st.selectbox("Provider", tuple(PROVIDER_PATHS))
        model = "nvidia/nemotron-3-ultra-550b-a55b:free"
        base_url = "https://openrouter.ai/api/v1"
        api_key = ""

        if provider == "Ollama":
            model = st.text_input("Ollama model", value="llama3")
        elif provider == "OpenAI-compatible API":
            base_url = st.text_input("Model API URL", value=base_url)
            api_key = st.text_input("API key", type="password")
            model = st.text_input("Model name", value="gpt-4o-mini")

        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_new_tokens = 128
        if provider == "Local Hugging Face":
            max_new_tokens = st.slider("Maximum new tokens", 1, 512, 128)

    messages = st.session_state.setdefault("messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Send a message")
    if not prompt:
        return

    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = build_payload(
        provider=provider,
        prompt=prompt,
        temperature=temperature,
        model=model,
        max_new_tokens=max_new_tokens,
        base_url=base_url,
        api_key=api_key,
    )
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream_response(api_base_url, provider, payload))
        except (httpx.HTTPError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Request failed: {exc}")
        else:
            messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()