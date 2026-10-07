"""Local Transformers-backed inference adapter."""

import asyncio
import threading
from typing import AsyncGenerator

from fastapi import HTTPException
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from app.core.engines.base import BaseInferenceEngine
from app.schemas.inference import LocalHFRequest, StreamChunk


class HuggingFaceEngine(BaseInferenceEngine):
    """Load a causal language model and stream generated text tokens."""

    def __init__(self, model_id: str = "Qwen/Qwen2.5-0.5B-Instruct") -> None:
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self._is_loaded = False

    def load_model(self):
        """Loads weights into memory/RAM. Called once during FastAPI lifespan."""
        if self._is_loaded:
            return

        print(f"[HuggingFace] Loading {self.model_id}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        self.model.eval()
        self._is_loaded = True
        print(f"[HuggingFace] {self.model_id} loaded successfully.")

    async def stream_generate(self, req: LocalHFRequest) -> AsyncGenerator[StreamChunk, None]:
        """Run generation on a worker thread while yielding decoded tokens."""
        if not self._is_loaded or self.model is None or self.tokenizer is None:
            yield StreamChunk(
                token="",
                is_finished=True,
                error="Model is not loaded. Ensure lifespan startup has completed."
            )
            return

        model_input = self.tokenizer(req.prompt, return_tensors="pt")

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_input,
            streamer=streamer,
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            do_sample=True if req.temperature > 0 else False
        )

        assert self.model is not None, "Model is not initialized"
        target_func = getattr(self.model, "generate")

        worker = threading.Thread(
            target=target_func,
            kwargs=generation_kwargs,
            name="HF-Inference-worker"
        )
        worker.daemon = True
        worker.start()

        def _get_next_token():
            try:
                return next(streamer)
            except StopIteration:
                return None

        try:
            while True:
                token = await asyncio.to_thread(_get_next_token)

                if token is None:
                    yield StreamChunk(token="", is_finished=True)
                    break
                yield StreamChunk(token=token, is_finished=False)
        except Exception as e:
            yield StreamChunk(token="", is_finished=True, error=str(e))

        finally:
            if worker.is_alive():
                worker.join()

        
