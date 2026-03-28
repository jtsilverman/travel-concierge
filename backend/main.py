import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.config import validate_keys
from backend import models
from backend.chat import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    await models.init_db()
    yield


app = FastAPI(title="Travel Concierge", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "api_keys": validate_keys()}


# --- Trips ---

class CreateTripRequest(BaseModel):
    name: str
    start_date: str
    end_date: str


@app.post("/api/trips")
async def create_trip(req: CreateTripRequest):
    return await models.create_trip(req.name, req.start_date, req.end_date)


@app.get("/api/trips")
async def list_trips():
    return await models.list_trips()


@app.get("/api/trips/{trip_id}")
async def get_trip(trip_id: str):
    trip = await models.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.delete("/api/trips/{trip_id}")
async def delete_trip(trip_id: str):
    await models.delete_trip(trip_id)
    return {"deleted": True}


# --- Itinerary Events ---

class CreateEventRequest(BaseModel):
    date: str
    title: str
    type: str
    time: str | None = None
    end_time: str | None = None
    source: str = "manual"
    details: dict | None = None
    notes: str | None = None


class UpdateEventRequest(BaseModel):
    date: str | None = None
    title: str | None = None
    time: str | None = None
    end_time: str | None = None
    notes: str | None = None
    sort_order: int | None = None


@app.post("/api/trips/{trip_id}/events")
async def add_event(trip_id: str, req: CreateEventRequest):
    return await models.add_event(
        trip_id=trip_id,
        date=req.date,
        title=req.title,
        event_type=req.type,
        time=req.time,
        end_time=req.end_time,
        source=req.source,
        details=req.details,
        notes=req.notes,
    )


@app.put("/api/trips/{trip_id}/events/{event_id}")
async def update_event(trip_id: str, event_id: str, req: UpdateEventRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    result = await models.update_event(event_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@app.delete("/api/trips/{trip_id}/events/{event_id}")
async def delete_event(trip_id: str, event_id: str):
    await models.delete_event(event_id)
    return {"deleted": True}


# --- Chat ---

class ChatRequest(BaseModel):
    trip_id: str
    message: str


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    async def event_stream():
        async for event in chat(req.trip_id, req.message):
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- Costs ---

@app.get("/api/costs")
async def get_costs(trip_id: str | None = None):
    return await models.get_costs(trip_id)


# --- Profile ---

class UpdateProfileRequest(BaseModel):
    home_airport: str | None = None
    loyalty_programs: list | None = None
    preferences: dict | None = None


@app.get("/api/profile")
async def get_profile():
    return await models.get_profile()


@app.put("/api/profile")
async def update_profile(req: UpdateProfileRequest):
    return await models.update_profile(
        home_airport=req.home_airport,
        loyalty_programs=req.loyalty_programs,
        preferences=req.preferences,
    )


# --- Static Files (serve built frontend) ---

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.isdir(FRONTEND_DIR):
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
