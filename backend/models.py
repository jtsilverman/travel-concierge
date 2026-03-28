import aiosqlite
import json
import uuid
from datetime import datetime
from backend.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS itinerary_events (
    id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    time TEXT,
    end_time TEXT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    details TEXT,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
    role TEXT CHECK(role IN ('user', 'assistant')),
    content TEXT,
    tool_calls TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
    service TEXT,
    operation TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    home_airport TEXT DEFAULT 'ORD',
    loyalty_programs TEXT DEFAULT '[]',
    preferences TEXT DEFAULT '{}'
);
"""


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    # Ensure profile row exists
    await db.execute(
        "INSERT OR IGNORE INTO profile (id, home_airport, loyalty_programs, preferences) VALUES (1, 'ORD', '[]', '{}')"
    )
    await db.commit()
    await db.close()


# --- Trips ---

async def create_trip(name: str, start_date: str, end_date: str) -> dict:
    trip_id = str(uuid.uuid4())[:8]
    db = await get_db()
    await db.execute(
        "INSERT INTO trips (id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
        (trip_id, name, start_date, end_date),
    )
    await db.commit()
    await db.close()
    return {"id": trip_id, "name": name, "start_date": start_date, "end_date": end_date}


async def list_trips() -> list:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM trips ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]


async def get_trip(trip_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = await cursor.fetchone()
    if not row:
        await db.close()
        return None
    trip = dict(row)

    # Get itinerary events
    cursor = await db.execute(
        "SELECT * FROM itinerary_events WHERE trip_id = ? ORDER BY date, time, sort_order",
        (trip_id,),
    )
    events = [dict(r) for r in await cursor.fetchall()]
    for e in events:
        if e.get("details"):
            e["details"] = json.loads(e["details"])

    # Get messages
    cursor = await db.execute(
        "SELECT * FROM messages WHERE trip_id = ? ORDER BY created_at", (trip_id,)
    )
    messages = [dict(r) for r in await cursor.fetchall()]
    for m in messages:
        if m.get("tool_calls"):
            m["tool_calls"] = json.loads(m["tool_calls"])

    trip["events"] = events
    trip["messages"] = messages
    await db.close()
    return trip


async def delete_trip(trip_id: str):
    db = await get_db()
    await db.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    await db.commit()
    await db.close()


# --- Itinerary Events ---

async def add_event(
    trip_id: str,
    date: str,
    title: str,
    event_type: str,
    time: str | None = None,
    end_time: str | None = None,
    source: str = "manual",
    details: dict | None = None,
    notes: str | None = None,
) -> dict:
    event_id = str(uuid.uuid4())[:8]
    details_json = json.dumps(details) if details else None
    db = await get_db()
    await db.execute(
        """INSERT INTO itinerary_events (id, trip_id, date, time, end_time, title, type, source, details, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, trip_id, date, time, end_time, title, event_type, source, details_json, notes),
    )
    await db.commit()
    await db.close()
    return {
        "id": event_id, "trip_id": trip_id, "date": date, "time": time,
        "end_time": end_time, "title": title, "type": event_type,
        "source": source, "details": details, "notes": notes,
    }


async def update_event(event_id: str, **kwargs) -> dict | None:
    db = await get_db()
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k == "details" and v is not None:
            v = json.dumps(v)
        sets.append(f"{k} = ?")
        vals.append(v)
    vals.append(event_id)
    await db.execute(f"UPDATE itinerary_events SET {', '.join(sets)} WHERE id = ?", vals)
    await db.commit()
    cursor = await db.execute("SELECT * FROM itinerary_events WHERE id = ?", (event_id,))
    row = await cursor.fetchone()
    await db.close()
    if row:
        r = dict(row)
        if r.get("details"):
            r["details"] = json.loads(r["details"])
        return r
    return None


async def delete_event(event_id: str):
    db = await get_db()
    await db.execute("DELETE FROM itinerary_events WHERE id = ?", (event_id,))
    await db.commit()
    await db.close()


# --- Messages ---

async def add_message(trip_id: str, role: str, content: str, tool_calls: list | None = None) -> dict:
    tc_json = json.dumps(tool_calls) if tool_calls else None
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO messages (trip_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (trip_id, role, content, tc_json),
    )
    msg_id = cursor.lastrowid
    await db.commit()
    await db.close()
    return {"id": msg_id, "trip_id": trip_id, "role": role, "content": content, "tool_calls": tool_calls}


# --- Cost Entries ---

async def add_cost_entry(
    trip_id: str, service: str, operation: str,
    cost_usd: float, input_tokens: int = 0, output_tokens: int = 0,
) -> dict:
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO cost_entries (trip_id, service, operation, input_tokens, output_tokens, cost_usd)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (trip_id, service, operation, input_tokens, output_tokens, cost_usd),
    )
    entry_id = cursor.lastrowid
    await db.commit()
    await db.close()
    return {"id": entry_id, "service": service, "operation": operation, "cost_usd": cost_usd}


async def get_costs(trip_id: str | None = None) -> dict:
    db = await get_db()
    if trip_id:
        cursor = await db.execute(
            "SELECT service, SUM(cost_usd) as total, COUNT(*) as calls FROM cost_entries WHERE trip_id = ? GROUP BY service",
            (trip_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT service, SUM(cost_usd) as total, COUNT(*) as calls FROM cost_entries GROUP BY service"
        )
    rows = [dict(r) for r in await cursor.fetchall()]

    cursor = await db.execute(
        "SELECT SUM(cost_usd) as grand_total FROM cost_entries" + (" WHERE trip_id = ?" if trip_id else ""),
        (trip_id,) if trip_id else (),
    )
    total_row = await cursor.fetchone()
    grand_total = dict(total_row)["grand_total"] or 0.0

    await db.close()
    return {"by_service": rows, "total_usd": grand_total}


# --- Profile ---

async def get_profile() -> dict:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM profile WHERE id = 1")
    row = await cursor.fetchone()
    await db.close()
    if not row:
        return {"home_airport": "ORD", "loyalty_programs": [], "preferences": {}}
    p = dict(row)
    p["loyalty_programs"] = json.loads(p["loyalty_programs"])
    p["preferences"] = json.loads(p["preferences"])
    return p


async def update_profile(home_airport: str | None = None, loyalty_programs: list | None = None, preferences: dict | None = None) -> dict:
    db = await get_db()
    updates = []
    vals = []
    if home_airport is not None:
        updates.append("home_airport = ?")
        vals.append(home_airport)
    if loyalty_programs is not None:
        updates.append("loyalty_programs = ?")
        vals.append(json.dumps(loyalty_programs))
    if preferences is not None:
        updates.append("preferences = ?")
        vals.append(json.dumps(preferences))
    if updates:
        await db.execute(f"UPDATE profile SET {', '.join(updates)} WHERE id = 1", vals)
        await db.commit()
    await db.close()
    return await get_profile()
