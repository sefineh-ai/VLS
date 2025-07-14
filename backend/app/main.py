from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(title="VLS Backend", version="1.0.0")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Include API router (to be implemented)
app.include_router(api_router)
