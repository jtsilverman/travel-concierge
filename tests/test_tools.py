import asyncio
import json
from unittest.mock import patch, MagicMock
import pytest

# Mock API responses
MOCK_FLIGHTS_RESPONSE = {
    "best_flights": [
        {
            "flights": [
                {
                    "airline": "Delta",
                    "flight_number": "DL1234",
                    "departure_airport": {"id": "ORD", "time": "2026-04-18 07:30"},
                    "arrival_airport": {"id": "MIA", "time": "2026-04-18 11:45"},
                }
            ],
            "price": 247,
            "total_duration": 195,
        },
        {
            "flights": [
                {
                    "airline": "United",
                    "flight_number": "UA5678",
                    "departure_airport": {"id": "ORD", "time": "2026-04-18 10:00"},
                    "arrival_airport": {"id": "MIA", "time": "2026-04-18 14:30"},
                }
            ],
            "price": 198,
            "total_duration": 210,
        },
    ],
    "other_flights": [],
    "price_insights": {"lowest_price": 198, "typical_price_range": [220, 350]},
}

MOCK_HOTELS_RESPONSE = {
    "properties": [
        {
            "name": "Faena Miami Beach",
            "hotel_class": 5,
            "overall_rating": 4.7,
            "rate_per_night": {"lowest": "$450"},
            "total_rate": {"lowest": "$1800"},
            "amenities": ["Pool", "Spa", "Beach Access", "Restaurant"],
            "images": [{"thumbnail": "https://example.com/faena.jpg"}],
        },
        {
            "name": "The Setai",
            "hotel_class": 5,
            "overall_rating": 4.8,
            "rate_per_night": {"lowest": "$520"},
            "total_rate": {"lowest": "$2080"},
            "amenities": ["Pool", "Spa", "Ocean View"],
            "images": [{"thumbnail": "https://example.com/setai.jpg"}],
        },
    ]
}

MOCK_RESTAURANTS_RESPONSE = {
    "places": [
        {
            "displayName": {"text": "Carbone"},
            "formattedAddress": "49 Collins Ave, Miami Beach, FL",
            "rating": 4.5,
            "userRatingCount": 1200,
            "priceLevel": "PRICE_LEVEL_VERY_EXPENSIVE",
            "websiteUri": "https://carbonemiami.com",
            "googleMapsUri": "https://maps.google.com/carbone",
        },
        {
            "displayName": {"text": "Joe's Stone Crab"},
            "formattedAddress": "11 Washington Ave, Miami Beach, FL",
            "rating": 4.3,
            "userRatingCount": 5000,
            "priceLevel": "PRICE_LEVEL_EXPENSIVE",
        },
    ]
}


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _mock_urlopen(mock_data):
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps(mock_data).encode()
    return mock_resp


@patch("backend.tools.flights.SERPAPI_API_KEY", "test-key")
@patch("urllib.request.urlopen")
def test_search_flights(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen(MOCK_FLIGHTS_RESPONSE)

    from backend.tools.flights import search_flights
    result = run(search_flights("ORD", "MIA", "2026-04-18"))

    assert len(result["flights"]) == 2
    assert result["flights"][0]["airline"] == "Delta"
    assert result["flights"][0]["price"] == 247
    assert result["flights"][1]["airline"] == "United"
    assert result["origin"] == "ORD"
    assert result["destination"] == "MIA"
    assert result["price_insights"]["lowest"] == 198


@patch("backend.tools.hotels.SERPAPI_API_KEY", "test-key")
@patch("urllib.request.urlopen")
def test_search_hotels(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen(MOCK_HOTELS_RESPONSE)

    from backend.tools.hotels import search_hotels
    result = run(search_hotels("Miami Beach", "2026-04-18", "2026-04-22"))

    assert len(result["hotels"]) == 2
    assert result["hotels"][0]["name"] == "Faena Miami Beach"
    assert result["hotels"][0]["stars"] == 5
    assert result["hotels"][0]["price_per_night"] == 450
    assert result["hotels"][1]["name"] == "The Setai"


@patch("backend.tools.restaurants.GOOGLE_PLACES_API_KEY", "test-key")
@patch("urllib.request.urlopen")
def test_search_restaurants(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen(MOCK_RESTAURANTS_RESPONSE)

    from backend.tools.restaurants import search_restaurants
    result = run(search_restaurants("Miami Beach", "italian"))

    assert len(result["restaurants"]) == 2
    assert result["restaurants"][0]["name"] == "Carbone"
    assert result["restaurants"][0]["price_level"] == "$$$$"
    assert result["restaurants"][0]["rating"] == 4.5
    assert result["restaurants"][1]["name"] == "Joe's Stone Crab"


def test_flights_no_api_key():
    from backend.tools.flights import search_flights
    # With default empty key, should return error
    with patch("backend.tools.flights.SERPAPI_API_KEY", ""):
        result = run(search_flights("ORD", "MIA", "2026-04-18"))
        assert "error" in result
        assert result["flights"] == []


def test_restaurants_no_api_key():
    from backend.tools.restaurants import search_restaurants
    with patch("backend.tools.restaurants.GOOGLE_PLACES_API_KEY", ""):
        result = run(search_restaurants("Miami Beach"))
        assert "error" in result
        assert result["restaurants"] == []
