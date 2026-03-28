import json
import urllib.request
import urllib.parse
from backend.config import SERPAPI_API_KEY


async def search_hotels(location: str, check_in: str, check_out: str) -> dict:
    """Search hotels via SerpAPI Google Hotels."""
    if not SERPAPI_API_KEY:
        return {"error": "SERPAPI_API_KEY not configured", "hotels": []}

    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": 2,
        "sort_by": 3,
        "currency": "USD",
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_API_KEY,
    }

    url = f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "hotels": []}

    raw_hotels = data.get("properties", [])
    hotels = []
    for i, h in enumerate(raw_hotels[:10], 1):
        rate = h.get("rate_per_night", {})
        price_str = rate.get("lowest", rate.get("before_taxes_fees", ""))
        price = 0
        if price_str:
            price = int("".join(c for c in str(price_str) if c.isdigit()) or "0")

        images = h.get("images", [])
        photo_url = images[0].get("thumbnail", "") if images else ""

        hotels.append({
            "rank": i,
            "name": h.get("name", "Unknown"),
            "price_per_night": price,
            "total_price": h.get("total_rate", {}).get("lowest", ""),
            "rating": h.get("overall_rating", 0),
            "stars": h.get("hotel_class", 0),
            "photo_url": photo_url,
            "amenities": h.get("amenities", [])[:8],
            "check_in": check_in,
            "check_out": check_out,
        })

    return {
        "hotels": hotels,
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
    }
