from backend import models
from backend.config import (
    CLAUDE_INPUT_COST_PER_MTOK,
    CLAUDE_OUTPUT_COST_PER_MTOK,
    SERPAPI_COST_PER_SEARCH,
    GOOGLE_PLACES_COST_PER_REQ,
)


async def track_claude_cost(trip_id: str, input_tokens: int, output_tokens: int):
    input_cost = (input_tokens / 1_000_000) * CLAUDE_INPUT_COST_PER_MTOK
    output_cost = (output_tokens / 1_000_000) * CLAUDE_OUTPUT_COST_PER_MTOK
    total = input_cost + output_cost
    await models.add_cost_entry(
        trip_id=trip_id,
        service="claude",
        operation="chat",
        cost_usd=round(total, 6),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def track_tool_cost(trip_id: str, service: str, operation: str):
    cost = SERPAPI_COST_PER_SEARCH if service == "serpapi" else GOOGLE_PLACES_COST_PER_REQ
    await models.add_cost_entry(
        trip_id=trip_id,
        service=service,
        operation=operation,
        cost_usd=cost,
    )
