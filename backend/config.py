import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

DB_PATH = os.getenv("DB_PATH", "travel_concierge.db")

# Claude model for chat
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Cost rates
CLAUDE_INPUT_COST_PER_MTOK = 3.0   # $/million tokens
CLAUDE_OUTPUT_COST_PER_MTOK = 15.0  # $/million tokens
SERPAPI_COST_PER_SEARCH = 0.015
GOOGLE_PLACES_COST_PER_REQ = 0.017


def validate_keys():
    """Check which API keys are available."""
    status = {}
    status["anthropic"] = bool(ANTHROPIC_API_KEY)
    status["serpapi"] = bool(SERPAPI_API_KEY)
    status["google_places"] = bool(GOOGLE_PLACES_API_KEY)
    return status
