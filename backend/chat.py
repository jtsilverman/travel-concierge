import json
import anthropic
from backend.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from backend import models
from backend.tools import flights, hotels, restaurants
from backend.cost_tracker import track_claude_cost, track_tool_cost

TOOLS = [
    {
        "name": "search_flights",
        "description": "Search for flights between airports. Use when user asks about flights or getting somewhere.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin airport code (e.g., ORD)"},
                "destination": {"type": "string", "description": "Destination airport code (e.g., MIA)"},
                "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                "return_date": {"type": "string", "description": "YYYY-MM-DD, omit for one-way"},
            },
            "required": ["origin", "destination", "departure_date"],
        },
    },
    {
        "name": "search_hotels",
        "description": "Search for hotels in an area. Use when user asks about where to stay.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or area"},
                "check_in": {"type": "string", "description": "YYYY-MM-DD"},
                "check_out": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["location", "check_in", "check_out"],
        },
    },
    {
        "name": "search_restaurants",
        "description": "Search for restaurants. Use when user asks about dining or where to eat.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Area to search"},
                "cuisine": {"type": "string", "description": "Optional cuisine filter"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "add_to_itinerary",
        "description": "Add a recommended item to the trip itinerary. Use after presenting search results when the user confirms they want to add something.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM (optional)"},
                "title": {"type": "string", "description": "Event title"},
                "type": {"type": "string", "enum": ["flight", "hotel", "restaurant", "activity"]},
                "details": {"type": "object", "description": "Structured data (price, rating, etc.)"},
            },
            "required": ["date", "title", "type"],
        },
    },
]


async def build_system_prompt(trip_id: str) -> str:
    trip = await models.get_trip(trip_id)
    profile = await models.get_profile()

    itinerary_text = "Empty - no events yet."
    if trip and trip.get("events"):
        lines = []
        current_date = None
        for e in trip["events"]:
            if e["date"] != current_date:
                current_date = e["date"]
                lines.append(f"\n{current_date}:")
            time_str = f" {e['time']}" if e.get("time") else ""
            lines.append(f"  {time_str} {e['title']} ({e['type']})")
        itinerary_text = "\n".join(lines)

    trip_name = trip["name"] if trip else "New Trip"
    dates = f"{trip['start_date']} to {trip['end_date']}" if trip else "TBD"

    return f"""You are a luxury travel concierge helping plan a trip: "{trip_name}" ({dates}).

Use your tools to search for real flights, hotels, and restaurants. Be opinionated -- recommend your top picks with clear reasoning. When the user likes an option, use add_to_itinerary to add it to their schedule.

Traveler profile:
- Home airport: {profile['home_airport']}
- Loyalty programs: {', '.join(profile['loyalty_programs']) or 'None'}
- Preferences: {json.dumps(profile['preferences']) if profile['preferences'] else 'None set'}

Current itinerary:
{itinerary_text}

Always search before answering travel questions -- don't guess at prices or availability. Reference the current itinerary when suggesting times to avoid conflicts."""


async def execute_tool(tool_name: str, tool_input: dict, trip_id: str) -> dict:
    """Execute a tool and return the result."""
    if tool_name == "search_flights":
        result = await flights.search_flights(**tool_input)
        await track_tool_cost(trip_id, "serpapi", "search_flights")
        return result
    elif tool_name == "search_hotels":
        result = await hotels.search_hotels(**tool_input)
        await track_tool_cost(trip_id, "serpapi", "search_hotels")
        return result
    elif tool_name == "search_restaurants":
        result = await restaurants.search_restaurants(**tool_input)
        await track_tool_cost(trip_id, "google_places", "search_restaurants")
        return result
    elif tool_name == "add_to_itinerary":
        event = await models.add_event(
            trip_id=trip_id,
            date=tool_input["date"],
            title=tool_input["title"],
            event_type=tool_input["type"],
            time=tool_input.get("time"),
            source="ai",
            details=tool_input.get("details"),
        )
        return {"added": True, "event": event}
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def chat(trip_id: str, user_message: str):
    """Run the chat loop with Claude, yielding SSE events.

    Yields dicts with: {"event": "text|tool_use|tool_result|itinerary_update|done", "data": {...}}
    """
    if not ANTHROPIC_API_KEY:
        yield {"event": "text", "data": {"content": "Error: ANTHROPIC_API_KEY not configured. Add it to your .env file."}}
        yield {"event": "done", "data": {}}
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Save user message
    await models.add_message(trip_id, "user", user_message)

    # Build conversation history
    trip = await models.get_trip(trip_id)
    conversation_messages = []
    if trip:
        for msg in trip.get("messages", []):
            if msg["role"] == "user":
                conversation_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                conversation_messages.append({"role": "assistant", "content": msg["content"]})

    # Ensure we have the current user message
    if not conversation_messages or conversation_messages[-1].get("content") != user_message:
        conversation_messages.append({"role": "user", "content": user_message})

    system_prompt = await build_system_prompt(trip_id)

    # Tool use loop (max 5 iterations to prevent infinite loops)
    full_response = ""
    tool_calls_data = []

    for _ in range(5):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=conversation_messages,
        )

        # Track Claude costs
        await track_claude_cost(
            trip_id,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        # Process response blocks
        has_tool_use = False
        tool_results = []

        for block in response.content:
            if block.type == "text":
                full_response += block.text
                yield {"event": "text", "data": {"content": block.text}}

            elif block.type == "tool_use":
                has_tool_use = True
                yield {"event": "tool_use", "data": {"tool": block.name, "input": block.input, "id": block.id}}

                # Execute the tool
                result = await execute_tool(block.name, block.input, trip_id)
                tool_calls_data.append({"tool": block.name, "input": block.input, "result": result})

                yield {"event": "tool_result", "data": {"tool": block.name, "result": result}}

                if block.name == "add_to_itinerary":
                    yield {"event": "itinerary_update", "data": result.get("event", {})}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        if not has_tool_use:
            break

        # Continue conversation with tool results
        conversation_messages.append({"role": "assistant", "content": response.content})
        conversation_messages.append({"role": "user", "content": tool_results})

    # Save assistant response
    await models.add_message(trip_id, "assistant", full_response, tool_calls_data if tool_calls_data else None)

    # Get final costs
    costs = await models.get_costs(trip_id)
    yield {"event": "done", "data": {"cost": costs}}
