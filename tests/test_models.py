import asyncio
import os
import pytest
from backend import models

TEST_DB = "test_travel.db"


@pytest.fixture(autouse=True)
def setup_db():
    """Use a test database and clean up after each test."""
    models.DB_PATH = TEST_DB
    asyncio.get_event_loop().run_until_complete(models.init_db())
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_create_and_list_trips():
    trip = run(models.create_trip("Miami Trip", "2026-04-18", "2026-04-22"))
    assert trip["name"] == "Miami Trip"
    assert trip["id"]

    trips = run(models.list_trips())
    assert len(trips) == 1
    assert trips[0]["name"] == "Miami Trip"


def test_get_trip_with_events_and_messages():
    trip = run(models.create_trip("Tokyo Trip", "2026-05-01", "2026-05-07"))

    run(models.add_event(
        trip["id"], "2026-05-01", "NRT → HND (ANA)", "flight",
        time="14:00", source="ai", details={"price": 850, "airline": "ANA"},
    ))
    run(models.add_event(
        trip["id"], "2026-05-02", "Brunch with friends", "custom",
        time="11:00", source="manual",
    ))
    run(models.add_message(trip["id"], "user", "Find flights to Tokyo"))
    run(models.add_message(trip["id"], "assistant", "Here are the options", tool_calls=[{"tool": "search_flights"}]))

    full = run(models.get_trip(trip["id"]))
    assert full["name"] == "Tokyo Trip"
    assert len(full["events"]) == 2
    assert full["events"][0]["details"]["airline"] == "ANA"
    assert len(full["messages"]) == 2
    assert full["messages"][1]["tool_calls"] == [{"tool": "search_flights"}]


def test_update_and_delete_event():
    trip = run(models.create_trip("Test", "2026-01-01", "2026-01-03"))
    event = run(models.add_event(trip["id"], "2026-01-01", "Dinner", "restaurant", time="19:00"))

    updated = run(models.update_event(event["id"], time="20:00", notes="Changed time"))
    assert updated["time"] == "20:00"
    assert updated["notes"] == "Changed time"

    run(models.delete_event(event["id"]))
    full = run(models.get_trip(trip["id"]))
    assert len(full["events"]) == 0


def test_cost_entries():
    trip = run(models.create_trip("Cost Test", "2026-01-01", "2026-01-03"))
    run(models.add_cost_entry(trip["id"], "claude", "chat", 0.02, input_tokens=5000, output_tokens=1000))
    run(models.add_cost_entry(trip["id"], "serpapi", "search_flights", 0.015))
    run(models.add_cost_entry(trip["id"], "claude", "chat", 0.03, input_tokens=8000, output_tokens=2000))

    costs = run(models.get_costs(trip["id"]))
    assert costs["total_usd"] == pytest.approx(0.065, abs=0.001)
    assert len(costs["by_service"]) == 2
    claude_row = next(r for r in costs["by_service"] if r["service"] == "claude")
    assert claude_row["calls"] == 2


def test_profile_crud():
    profile = run(models.get_profile())
    assert profile["home_airport"] == "ORD"
    assert profile["loyalty_programs"] == []

    updated = run(models.update_profile(
        home_airport="SFO",
        loyalty_programs=["Delta SkyMiles", "Marriott Bonvoy"],
        preferences={"budget": "moderate"},
    ))
    assert updated["home_airport"] == "SFO"
    assert "Delta SkyMiles" in updated["loyalty_programs"]
    assert updated["preferences"]["budget"] == "moderate"


def test_delete_trip_cascades():
    trip = run(models.create_trip("Delete Me", "2026-01-01", "2026-01-03"))
    run(models.add_event(trip["id"], "2026-01-01", "Event", "custom"))
    run(models.add_message(trip["id"], "user", "hello"))
    run(models.add_cost_entry(trip["id"], "claude", "chat", 0.01))

    run(models.delete_trip(trip["id"]))
    assert run(models.get_trip(trip["id"])) is None
    trips = run(models.list_trips())
    assert len(trips) == 0
