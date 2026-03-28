import json
import urllib.request
from backend.config import GOOGLE_PLACES_API_KEY

PRICE_MAP = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}


async def search_restaurants(location: str, cuisine: str | None = None) -> dict:
    """Search restaurants via Google Places API."""
    if not GOOGLE_PLACES_API_KEY:
        return {"error": "GOOGLE_PLACES_API_KEY not configured", "restaurants": []}

    query = f"{cuisine + ' ' if cuisine else ''}restaurant in {location}"

    url = "https://places.googleapis.com/v1/places:searchText"
    body = json.dumps({
        "textQuery": query,
        "maxResultCount": 8,
        "languageCode": "en",
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.websiteUri,places.googleMapsUri",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "restaurants": []}

    places = data.get("places", [])
    restaurants = []
    for i, p in enumerate(places, 1):
        restaurants.append({
            "rank": i,
            "name": p.get("displayName", {}).get("text", "Unknown"),
            "address": p.get("formattedAddress", ""),
            "rating": p.get("rating", 0),
            "review_count": p.get("userRatingCount", 0),
            "price_level": PRICE_MAP.get(p.get("priceLevel", ""), "N/A"),
            "cuisine": cuisine or "Various",
            "website": p.get("websiteUri", ""),
            "maps_url": p.get("googleMapsUri", ""),
        })

    return {
        "restaurants": restaurants,
        "location": location,
        "cuisine": cuisine,
    }
