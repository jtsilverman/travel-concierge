import asyncio
import os
import pytest
from backend import models
from backend.cost_tracker import track_claude_cost, track_tool_cost

TEST_DB = "test_cost.db"


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def setup_db():
    models.DB_PATH = TEST_DB
    run(models.init_db())
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_track_claude_cost():
    trip = run(models.create_trip("Test", "2026-01-01", "2026-01-03"))

    # 5000 input tokens at $3/MTok = $0.015
    # 1000 output tokens at $15/MTok = $0.015
    # Total = $0.030
    run(track_claude_cost(trip["id"], 5000, 1000))

    costs = run(models.get_costs(trip["id"]))
    assert costs["total_usd"] == pytest.approx(0.030, abs=0.001)
    assert costs["by_service"][0]["service"] == "claude"


def test_track_tool_cost_serpapi():
    trip = run(models.create_trip("Test", "2026-01-01", "2026-01-03"))
    run(track_tool_cost(trip["id"], "serpapi", "search_flights"))

    costs = run(models.get_costs(trip["id"]))
    assert costs["total_usd"] == pytest.approx(0.015, abs=0.001)


def test_track_tool_cost_google_places():
    trip = run(models.create_trip("Test", "2026-01-01", "2026-01-03"))
    run(track_tool_cost(trip["id"], "google_places", "search_restaurants"))

    costs = run(models.get_costs(trip["id"]))
    assert costs["total_usd"] == pytest.approx(0.017, abs=0.001)


def test_aggregate_costs():
    trip = run(models.create_trip("Test", "2026-01-01", "2026-01-03"))
    run(track_claude_cost(trip["id"], 5000, 1000))  # ~$0.030
    run(track_tool_cost(trip["id"], "serpapi", "search_flights"))  # $0.015
    run(track_tool_cost(trip["id"], "serpapi", "search_hotels"))  # $0.015
    run(track_tool_cost(trip["id"], "google_places", "search_restaurants"))  # $0.017

    costs = run(models.get_costs(trip["id"]))
    assert costs["total_usd"] == pytest.approx(0.077, abs=0.001)
    assert len(costs["by_service"]) == 3  # claude, serpapi, google_places

    serpapi = next(r for r in costs["by_service"] if r["service"] == "serpapi")
    assert serpapi["calls"] == 2
