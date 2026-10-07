from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.routes import router
from app.core.engines.huggingface import HuggingFaceEngine
from app.core.engines.ollama import OllamaEngine
from app.core.engines.openai_compatible import OpenAIEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n--- Starting Gateway: Initializing Engine ---")

    app.state.ollama_engine = OllamaEngine()
    app.state.openai_engine = OpenAIEngine()
    app.state.hf_engine = HuggingFaceEngine(model_id="Qwen/Qwen2.5-0.5B-Instruct")
    app.state.hf_engine.load_model()

    print("--- All Engines are Ready to Serve the Traffic ---\n")
    yield
    print("\n--- Shutting Down Gateway ---")

app = FastAPI(title="Modular Inference Gateway", lifespan=lifespan)
app.include_router(router=router)

@app.get("/health", status_code=200, tags=['Health'])
def health_check() -> dict:
    return {
        "status": "healthy",
        "message": "applicaion is running"
    }