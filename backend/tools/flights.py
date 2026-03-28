import json
import urllib.request
import urllib.parse
from backend.config import SERPAPI_API_KEY


def _format_flight(flight, idx):
    legs = flight.get("flights", [])
    price = flight.get("price", 0)
    total_dur = flight.get("total_duration", 0)
    stops = len(legs) - 1
    airline = legs[0].get("airline", "Unknown") if legs else "Unknown"
    flight_no = legs[0].get("flight_number", "") if legs else ""
    dep = legs[0].get("departure_airport", {}) if legs else {}
    arr = legs[-1].get("arrival_airport", {}) if legs else {}
    dep_time = dep.get("time", "").split(" ")[-1] if dep.get("time") else ""
    arr_time = arr.get("time", "").split(" ")[-1] if arr.get("time") else ""

    hours = total_dur // 60
    mins = total_dur % 60
    duration = f"{hours}h{mins:02d}m" if hours else f"{mins}m"

    return {
        "rank": idx,
        "airline": airline,
        "flight_no": flight_no,
        "price": price,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "duration": duration,
        "stops": stops,
        "from_airport": dep.get("id", ""),
        "to_airport": arr.get("id", ""),
        "booking_url": f"https://www.google.com/travel/flights",
    }


async def search_flights(origin: str, destination: str, departure_date: str, return_date: str | None = None) -> dict:
    """Search flights via SerpAPI Google Flights."""
    if not SERPAPI_API_KEY:
        return {"error": "SERPAPI_API_KEY not configured", "flights": []}

    params = {
        "engine": "google_flights",
        "departure_id": origin.upper(),
        "arrival_id": destination.upper(),
        "outbound_date": departure_date,
        "currency": "USD",
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }
    if return_date:
        params["return_date"] = return_date

    url = f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "flights": []}

    best = data.get("best_flights", [])
    other = data.get("other_flights", [])
    flights = []
    for i, f in enumerate(best + other[:5], 1):
        flights.append(_format_flight(f, i))

    price_insights = data.get("price_insights", {})
    return {
        "flights": flights,
        "price_insights": {
            "lowest": price_insights.get("lowest_price"),
            "typical_range": price_insights.get("typical_price_range"),
        },
        "trip_type": "round_trip" if return_date else "one_way",
        "origin": origin.upper(),
        "destination": destination.upper(),
    }
