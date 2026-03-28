# Travel Concierge Web App -- MVP Spec

## Overview

Self-hostable travel planning web app powered by Claude API with tool use. The core is an **interactive itinerary timeline** that you build through conversation with an AI concierge. Chat to search real flights, hotels, restaurants, and activities, and the AI adds them to your day-by-day schedule. Manually add custom events (brunch with family, beach morning, etc.) alongside AI-searched items. The itinerary is the product -- a visual, editable trip plan you build collaboratively with AI.

The twist: no self-hostable AI travel planner exists (Layla, Stardrift, Mindtrip are all SaaS), and none let you mix AI-searched results with custom events on the same timeline. Deploy with your own Claude API key + free-tier travel APIs. Built-in cost tracking shows exactly what each trip plan costs (~$0.30/trip).

## Scope

- **Timebox:** 3 days
- **Building:**
  - Split-pane UI: chat panel (left) + itinerary timeline (right)
  - Claude tool use: search_flights, search_hotels, search_restaurants, add_to_itinerary tools
  - Day-by-day itinerary timeline with time slots, icons by event type, drag-to-reorder
  - Manual event adding: custom events with title, time, notes (no AI needed)
  - Structured result cards in chat: flight tables, hotel cards, restaurant cards
  - "Add to itinerary" button on each result card
  - Trip management: create/name trips with date ranges, switch between trips
  - Traveler profile (home airport, loyalty programs, preferences)
  - Cost tracking: per-trip API costs (Claude tokens, SerpAPI, Google Places)
  - Conversation history per trip (SQLite)
  - Self-hostable: single `docker compose up` with env vars for API keys
- **Not building:** User auth (single-user), booking/payments, map integration, multi-user collaboration, PDF/calendar export, mobile-responsive layout
- **Ship target:** GitHub + Docker Compose

## Project Type

**Hybrid** -- Claude API agent with tool use (agent layer) + web app (code layer)

## Stack

- **Backend:** Python 3.12 + FastAPI + Anthropic SDK (tool use, streaming)
- **Frontend:** React + TypeScript + Vite (first React project in portfolio)
- **Database:** SQLite via aiosqlite (trips, itinerary events, conversations, cost tracking)
- **Travel APIs:** Reuse existing Python scripts from ~/Rock/workspaces/travel/scripts/ (SerpAPI, Google Places)
- **Deployment:** Docker Compose (FastAPI serves built React static files)
- **Why this stack:** Python backend reuses existing travel scripts. React+TS adds portfolio diversity (no React project yet). SQLite keeps it self-hostable.

## Architecture

### File Structure
```
travel-concierge/
  backend/
    main.py              -- FastAPI app, CORS, static serving
    chat.py              -- Claude API integration, tool dispatch, streaming
    tools/
      __init__.py
      flights.py         -- search_flights tool
      hotels.py          -- search_hotels tool
      restaurants.py     -- search_restaurants tool
    models.py            -- SQLite: Trip, ItineraryEvent, Message, CostEntry, Profile
    cost_tracker.py      -- API cost tracking
    config.py            -- Env var loading
  frontend/
    src/
      App.tsx            -- Main layout: chat (left) + itinerary (right)
      components/
        ChatPanel.tsx    -- Chat messages + input
        MessageBubble.tsx -- Message with optional result cards
        FlightCard.tsx   -- Flight comparison card with "Add to itinerary" button
        HotelCard.tsx    -- Hotel card with "Add to itinerary" button
        RestaurantCard.tsx -- Restaurant card with "Add to itinerary" button
        Itinerary.tsx    -- Day-by-day timeline view
        DayColumn.tsx    -- Single day with time-slot events
        EventCard.tsx    -- Individual event on the timeline (flight/hotel/meal/custom)
        AddEventModal.tsx -- Manual event creation form
        TripSidebar.tsx  -- Trip list, create trip, profile, cost summary
      hooks/
        useChat.ts       -- Chat state, SSE streaming
        useTrip.ts       -- Trip + itinerary CRUD
      types.ts           -- TypeScript interfaces
    index.html
    vite.config.ts
    package.json
  docker-compose.yml
  Dockerfile
  requirements.txt
  tests/
    test_tools.py
    test_chat.py
    test_models.py
    test_e2e.py
```

### Data Models (SQLite)
```sql
CREATE TABLE trips (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,              -- "Miami Spring Break"
  start_date TEXT NOT NULL,        -- "2026-04-18"
  end_date TEXT NOT NULL,          -- "2026-04-22"
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itinerary_events (
  id TEXT PRIMARY KEY,
  trip_id TEXT REFERENCES trips(id),
  date TEXT NOT NULL,              -- "2026-04-18"
  time TEXT,                       -- "07:30" (optional for all-day events)
  end_time TEXT,                   -- "11:30" (optional)
  title TEXT NOT NULL,             -- "ORD → MIA (Delta)" or "Brunch with family"
  type TEXT NOT NULL,              -- 'flight', 'hotel', 'restaurant', 'activity', 'custom'
  source TEXT DEFAULT 'manual',    -- 'ai' or 'manual'
  details TEXT,                    -- JSON: structured data (price, airline, rating, etc.)
  notes TEXT,                      -- User notes
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT REFERENCES trips(id),
  role TEXT CHECK(role IN ('user', 'assistant')),
  content TEXT,
  tool_calls TEXT,                 -- JSON: tool use data for rendering cards
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT REFERENCES trips(id),
  service TEXT,
  operation TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profile (
  id INTEGER PRIMARY KEY CHECK(id = 1),
  home_airport TEXT DEFAULT 'ORD',
  loyalty_programs TEXT DEFAULT '[]',
  preferences TEXT DEFAULT '{}'
);
```

### API Contracts

**POST /api/chat**
```json
Request: { "trip_id": "abc", "message": "Find flights from ORD to MIA April 18" }
Response: SSE stream (text, tool_use, tool_result, done events)
```

**Trips:**
- POST /api/trips -- create trip {name, start_date, end_date}
- GET /api/trips -- list trips
- GET /api/trips/:id -- trip with itinerary + messages

**Itinerary:**
- POST /api/trips/:id/events -- add event (manual or from AI result)
- PUT /api/trips/:id/events/:eid -- update event (reorder, edit)
- DELETE /api/trips/:id/events/:eid -- remove event

**Other:**
- GET /api/costs?trip_id=abc -- cost data
- GET/PUT /api/profile -- traveler profile

### Claude Tool Definitions
```python
tools = [
    {
        "name": "search_flights",
        "description": "Search for flights between airports. Use when user asks about flights or getting somewhere.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin airport code"},
                "destination": {"type": "string", "description": "Destination airport code"},
                "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                "return_date": {"type": "string", "description": "YYYY-MM-DD (optional)"},
            },
            "required": ["origin", "destination", "departure_date"]
        }
    },
    {
        "name": "search_hotels",
        "description": "Search for hotels in an area. Use when user asks about where to stay.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "check_in": {"type": "string", "description": "YYYY-MM-DD"},
                "check_out": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["location", "check_in", "check_out"]
        }
    },
    {
        "name": "search_restaurants",
        "description": "Search for restaurants. Use when user asks about dining or where to eat.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "cuisine": {"type": "string", "description": "Optional cuisine filter"},
            },
            "required": ["location"]
        }
    },
    {
        "name": "add_to_itinerary",
        "description": "Add a recommended item to the trip itinerary. Use after presenting search results when the user confirms they want to add something.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM (optional)"},
                "title": {"type": "string"},
                "type": {"type": "string", "enum": ["flight", "hotel", "restaurant", "activity"]},
                "details": {"type": "object", "description": "Structured data (price, rating, etc.)"},
            },
            "required": ["date", "title", "type"]
        }
    }
]
```

### System Prompt
```
You are a luxury travel concierge helping plan a trip: "{trip.name}" ({trip.start_date} to {trip.end_date}).

Use your tools to search for real flights, hotels, and restaurants. Be opinionated -- recommend your top picks with clear reasoning. When the user likes an option, use add_to_itinerary to add it to their schedule.

Traveler profile:
- Home airport: {profile.home_airport}
- Loyalty programs: {profile.loyalty_programs}
- Preferences: {profile.preferences}

Current itinerary:
{formatted_itinerary}

Always search before answering -- don't guess at prices or availability. Reference the current itinerary when suggesting times to avoid conflicts.
```

## Task List

### Phase 1: Backend Foundation

#### Task 1.1: Project scaffold + config
**Files:** `backend/__init__.py` (create), `backend/main.py` (create), `backend/config.py` (create), `requirements.txt` (create)
**Do:** Initialize FastAPI app with CORS. Config loads env vars: ANTHROPIC_API_KEY, SERPAPI_API_KEY, GOOGLE_PLACES_API_KEY. Health check endpoint at GET /api/health. Requirements: fastapi, uvicorn, anthropic, aiosqlite, python-dotenv.
**Validate:** `pip install -r requirements.txt && uvicorn backend.main:app --port 8000 & sleep 2 && curl -s http://localhost:8000/api/health && kill %1`

#### Task 1.2: Database models
**Files:** `backend/models.py` (create), `tests/test_models.py` (create)
**Do:** SQLite setup with aiosqlite. Create all tables (trips, itinerary_events, messages, cost_entries, profile). CRUD functions for each table. Auto-create tables on first call.
**Validate:** `python -m pytest tests/test_models.py -v`

#### Task 1.3: Travel tool functions
**Files:** `backend/tools/__init__.py` (create), `backend/tools/flights.py` (create), `backend/tools/hotels.py` (create), `backend/tools/restaurants.py` (create), `tests/test_tools.py` (create)
**Do:** Adapt existing travel scripts into async tool functions with normalized response formats. Each returns structured data for both Claude tool results and frontend cards. Include cached/mock responses for testing.
**Validate:** `python -m pytest tests/test_tools.py -v`

### Phase 2: Chat + API Endpoints

#### Task 2.1: Chat engine with tool use + streaming
**Files:** `backend/chat.py` (create), `tests/test_chat.py` (create)
**Do:** Claude API integration with streaming + tool use loop. Define 4 tools (flights, hotels, restaurants, add_to_itinerary). Handle tool dispatch, itinerary mutations, and SSE event formatting. Load trip context + profile into system prompt.
**Validate:** `python -m pytest tests/test_chat.py -v`

#### Task 2.2: Cost tracker
**Files:** `backend/cost_tracker.py` (create), `tests/test_cost.py` (create)
**Do:** Track Claude token costs (Sonnet pricing: $3/$15 per MTok), SerpAPI calls, Google Places calls. Per-trip aggregation.
**Validate:** `python -m pytest tests/test_cost.py -v`

#### Task 2.3: API endpoints
**Files:** `backend/main.py` (modify)
**Do:** Wire up all endpoints: POST /api/chat (SSE), trips CRUD, itinerary events CRUD, costs, profile.
**Validate:** `uvicorn backend.main:app --port 8000 & sleep 2 && curl -s http://localhost:8000/api/trips | python3.12 -m json.tool && kill %1`

### Phase 3: React Frontend

#### Task 3.1: React scaffold + types
**Files:** `frontend/` (create via Vite), `frontend/src/types.ts` (create)
**Do:** Initialize React+TS with Vite. Define TypeScript interfaces. Vite proxy to localhost:8000. Dark theme CSS variables.
**Validate:** `cd frontend && npm install && npm run build`

#### Task 3.2: Chat panel + streaming
**Files:** `frontend/src/App.tsx`, `frontend/src/components/ChatPanel.tsx`, `frontend/src/components/MessageBubble.tsx`, `frontend/src/hooks/useChat.ts`
**Do:** Chat UI with SSE streaming. Split-pane layout: chat left, itinerary right. Show streaming text as it arrives. Render tool_use/tool_result events with structured cards.
**Validate:** `cd frontend && npm run build`

#### Task 3.3: Result cards with "Add to itinerary"
**Files:** `frontend/src/components/FlightCard.tsx`, `frontend/src/components/HotelCard.tsx`, `frontend/src/components/RestaurantCard.tsx`
**Do:** Structured result cards. Each has an "Add to itinerary" button that calls POST /api/trips/:id/events (or tells Claude to use add_to_itinerary tool). FlightCard: airline, times, duration, stops, price. HotelCard: photo, name, stars, price/night, amenities. RestaurantCard: photo, name, cuisine, price level, rating.
**Validate:** `cd frontend && npm run build`

#### Task 3.4: Itinerary timeline
**Files:** `frontend/src/components/Itinerary.tsx`, `frontend/src/components/DayColumn.tsx`, `frontend/src/components/EventCard.tsx`, `frontend/src/components/AddEventModal.tsx`, `frontend/src/hooks/useTrip.ts`
**Do:** Day-by-day timeline view. Each day is a column with time-sorted events. EventCard shows icon by type (plane, bed, fork, star, calendar), title, time, price. Color-coded: AI-sourced (blue border) vs manual (gray border). "+" button opens AddEventModal for custom events (title, date, time, notes). useTrip hook manages trip state and itinerary CRUD.
**Validate:** `cd frontend && npm run build`

#### Task 3.5: Trip sidebar + profile + costs
**Files:** `frontend/src/components/TripSidebar.tsx`, `frontend/src/components/ProfileSetup.tsx`, `frontend/src/components/CostDashboard.tsx`
**Do:** Collapsible left sidebar: trip list, "New Trip" button (name + date picker), profile button, cost summary. ProfileSetup: modal with home airport, loyalty programs, preferences. CostDashboard: expandable panel showing per-trip API costs.
**Validate:** `cd frontend && npm run build`

### Phase 4: Integration + Docker

#### Task 4.1: Full integration + static serving
**Files:** `backend/main.py` (modify)
**Do:** Serve frontend dist/ as static files from FastAPI. SQLite auto-init on startup. Test full flow: create trip, chat, search, add to itinerary, view timeline.
**Validate:** `cd frontend && npm run build && cd .. && uvicorn backend.main:app --port 8000` -- full app works at localhost:8000

#### Task 4.2: Docker Compose
**Files:** `Dockerfile` (create), `docker-compose.yml` (create), `.dockerignore` (create)
**Do:** Multi-stage Dockerfile (Node builds frontend, Python runs backend). docker-compose.yml with env vars, SQLite volume.
**Validate:** `docker compose build && docker compose up -d && sleep 5 && curl -s http://localhost:8000/api/health && docker compose down`

#### Task 4.3: End-to-end tests
**Files:** `tests/test_e2e.py` (create)
**Do:** Full integration tests: create trip, chat with tool use, verify itinerary event created, verify costs tracked, test manual event CRUD, test profile persistence.
**Validate:** `python -m pytest tests/test_e2e.py -v`

### Phase 5: Ship

#### Task 5.1: README + deploy
**Files:** `README.md` (create)
**Do:** README with: problem (no self-hostable AI travel planner), demo screenshot, docker compose setup, env vars, features, cost breakdown (~$0.30/trip), tech stack, the hard part. Push to GitHub as jtsilverman/travel-concierge. Deploy live demo to GitHub Pages (static screenshot) or Railway.
**Validate:** `gh repo view jtsilverman/travel-concierge`

## The One Hard Thing

**Claude tool use streaming + itinerary mutations.** Three challenges in one:

1. **Streaming tool use loop:** Claude starts responding, requests a tool (search_flights), we execute it, feed the result back, Claude continues. The Anthropic SDK handles this but mapping the event stream (content_block_start/delta/stop) to frontend SSE events requires careful state management.

2. **AI-driven itinerary mutations:** Claude's add_to_itinerary tool modifies the database mid-conversation. The frontend needs to detect this and update the timeline in real-time without a page refresh. The system prompt includes the current itinerary so Claude avoids scheduling conflicts.

3. **Mixed content rendering:** The chat shows both conversational text AND structured cards (flight tables, hotel cards), AND the timeline updates simultaneously. The frontend needs to handle all three event types from a single SSE stream.

**Approach:** Backend emits typed SSE events (text, tool_use, tool_result, itinerary_update, done). Frontend useChat hook dispatches to message state (for chat) and trip state (for itinerary) based on event type. The add_to_itinerary tool handler writes to SQLite and emits an itinerary_update event.

**Fallback:** Non-streaming mode. Send message, wait for full response, return complete result with any itinerary changes. Manual "Add to itinerary" buttons on result cards as primary flow instead of Claude auto-adding.

## Risks

- **Medium -- ANTHROPIC_API_KEY not on Mac Mini.** Jake needs to add it. Without it, chat won't work.
- **Medium -- SerpAPI free tier (100/month).** Cache during dev, mock in tests.
- **Medium -- Scope.** Itinerary timeline + chat + cards + costs + profile is a lot for 3 days. Mitigation: timeline can be simple (vertical list, no drag-and-drop) for MVP. Polish later.
- **Low -- Claude tool use streaming.** Well-documented, fallback available.
- **Low -- React first project.** Keep it simple: hooks + CSS, no libraries.
