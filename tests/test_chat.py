import asyncio
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from backend import models

TEST_DB = "test_chat.db"


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def setup_db():
    models.DB_PATH = TEST_DB
    run(models.init_db())
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_build_system_prompt():
    from backend.chat import build_system_prompt

    trip = run(models.create_trip("Miami Trip", "2026-04-18", "2026-04-22"))
    run(models.add_event(trip["id"], "2026-04-18", "ORD -> MIA", "flight", time="07:30", source="ai"))
    run(models.update_profile(home_airport="ORD", loyalty_programs=["Delta SkyMiles"]))

    prompt = run(build_system_prompt(trip["id"]))
    assert "Miami Trip" in prompt
    assert "2026-04-18 to 2026-04-22" in prompt
    assert "ORD" in prompt
    assert "Delta SkyMiles" in prompt
    assert "ORD -> MIA" in prompt


def test_execute_tool_add_to_itinerary():
    from backend.chat import execute_tool

    trip = run(models.create_trip("Test", "2026-04-18", "2026-04-22"))
    result = run(execute_tool("add_to_itinerary", {
        "date": "2026-04-18",
        "time": "19:00",
        "title": "Dinner at Carbone",
        "type": "restaurant",
        "details": {"price_level": "$$$$", "rating": 4.5},
    }, trip["id"]))

    assert result["added"] is True
    assert result["event"]["title"] == "Dinner at Carbone"
    assert result["event"]["source"] == "ai"

    # Verify it's in the trip
    full_trip = run(models.get_trip(trip["id"]))
    assert len(full_trip["events"]) == 1
    assert full_trip["events"][0]["title"] == "Dinner at Carbone"


def test_execute_tool_search_flights_mock():
    from backend.chat import execute_tool

    trip = run(models.create_trip("Test", "2026-04-18", "2026-04-22"))

    mock_result = {"flights": [{"airline": "Delta", "price": 247}]}
    with patch("backend.chat.flights.search_flights", new_callable=AsyncMock, return_value=mock_result):
        with patch("backend.chat.track_tool_cost", new_callable=AsyncMock):
            result = run(execute_tool("search_flights", {
                "origin": "ORD",
                "destination": "MIA",
                "departure_date": "2026-04-18",
            }, trip["id"]))

    assert result["flights"][0]["airline"] == "Delta"


def test_execute_tool_unknown():
    from backend.chat import execute_tool

    trip = run(models.create_trip("Test", "2026-04-18", "2026-04-22"))
    result = run(execute_tool("unknown_tool", {}, trip["id"]))
    assert "error" in result


def test_chat_no_api_key():
    from backend.chat import chat

    trip = run(models.create_trip("Test", "2026-04-18", "2026-04-22"))

    events = []
    async def collect():
        async for event in chat(trip["id"], "hello"):
            events.append(event)

    with patch("backend.chat.ANTHROPIC_API_KEY", ""):
        run(collect())

    assert any(e["event"] == "text" and "not configured" in e["data"]["content"] for e in events)
    assert any(e["event"] == "done" for e in events)
