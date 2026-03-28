from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import validate_keys

app = FastAPI(title="Travel Concierge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    keys = validate_keys()
    return {"status": "ok", "api_keys": keys}
