from fastapi import FastAPI

app = FastAPI(title="Async handler")

@app.get("/health", status_code=200, tags=['Health'])
def health_check() -> dict:
    return {
        "status": "healthy",
        "message": "applicaion is running"
    }