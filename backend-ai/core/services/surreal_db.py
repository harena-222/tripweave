from __future__ import annotations
import os
from typing import Any
from surrealdb import AsyncSurreal
from contextlib import asynccontextmanager
try:
    from surrealdb import RecordID
except Exception:
    RecordID = None

# Create a global connection string from .env [cite: 2026-03-07]
DB_URL = os.getenv("SURREAL_DB_URL", "ws://localhost:8001/rpc")
SURREAL_USER = os.getenv("SURREAL_USER", "root")
SURREAL_PASS = os.getenv("SURREAL_PASS", "root")
SURREAL_NS = os.getenv("SURREAL_NS", "tripweave_ns")
SURREAL_DB = os.getenv("SURREAL_DB", "tripweave_db")

async def get_user_profile(traveller_id: str) -> dict[str, Any]:
    """
    Fetch the traveller profile from SurrealDB.
    Example traveller_id: "traveller:idiots"
    """
    async with AsyncSurreal(DB_URL) as db:
        await db.signin(
            {
                "username": SURREAL_USER,
                "password": SURREAL_PASS,
            }
        )
        await db.use(SURREAL_NS, SURREAL_DB)

        profile = await db.select(traveller_id)
        sanitised_profile = serialise_surreal_value(profile)
        print(f"--- [SurrealDB] Successfully fetched: {sanitised_profile} ---")

        return sanitised_profile or {"message": "Profile not found", "id": traveller_id}

@asynccontextmanager
async def get_db_connection():
    """helper function"""
    async with AsyncSurreal(DB_URL) as db:
        await db.signin({"username": SURREAL_USER, "password": SURREAL_PASS})
        await db.use(SURREAL_NS, SURREAL_DB)
        yield db

async def save_day_plan(day_plan_payload: dict) -> dict:
    day_plan_id = day_plan_payload["id"]
    data = {k: v for k, v in day_plan_payload.items() if k != "id"}

    print(f"--- [SurrealDB] save_day_plan called with id={day_plan_id} data={data} ---")

    async with AsyncSurreal(DB_URL) as db:
        await db.signin({
            "username": SURREAL_USER,
            "password": SURREAL_PASS,
        })
        await db.use(SURREAL_NS, SURREAL_DB)

        saved = await upsert_record(db, day_plan_id, data)
        print(f"--- [SurrealDB] save_day_plan result: {saved} ---")
        return saved

async def save_trip(trip_payload: dict) -> dict:
    trip_id = trip_payload["id"]
    data = {k: v for k, v in trip_payload.items() if k != "id"}

    print(f"--- [SurrealDB] save_trip called with id={trip_id} data={data} ---")

    async with AsyncSurreal(DB_URL) as db:
        await db.signin({
            "username": SURREAL_USER,
            "password": SURREAL_PASS,
        })
        await db.use(SURREAL_NS, SURREAL_DB)

        saved = await upsert_record(db, trip_id, data)
        print(f"--- [SurrealDB] Saved trip: {saved} ---")
        return saved

async def persist_relationship_updates(relationship_updates: list[dict]) -> None:
    async with AsyncSurreal(DB_URL) as db:
        await db.signin({
            "username": SURREAL_USER,
            "password": SURREAL_PASS,
        })
        await db.use(SURREAL_NS, SURREAL_DB)

        for update in relationship_updates:
            action = update["action"]
            relation = update["relation"]
            from_id = update["from"]
            to_id = update["to"]

            if action == "create":
                await db.query(f"RELATE {from_id}->{relation}->{to_id};")
            elif action == "remove":
                await db.query(f"DELETE {relation} WHERE out = {from_id} AND in = {to_id};")

async def save_preference_update(preference_payload: dict) -> dict:
    traveller_id = preference_payload["id"]
    data = {k: v for k, v in preference_payload.items() if k != "id"}
    async with get_db_connection() as db:
        return await upsert_record(db, traveller_id, data)

async def save_disruption(disruption_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Save a disruption record.
    Expected example:
    {
        "id": "disruption:weather_rain_afternoon",
        "type": "weather",
        "condition": "rain"
    }
    """
    disruption_id = disruption_payload["id"]
    data = {k: v for k, v in disruption_payload.items() if k != "id"}
    return await upsert_record(disruption_id, data)


async def save_decision(decision_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Save a decision record.
    Expected example:
    {
        "id": "decision:replan_001",
        "type": "replan",
        "reason": "rain affecting current plan",
        "summary": "Move activity to the next day..."
    }
    """
    decision_id = decision_payload["id"]
    data = {k: v for k, v in decision_payload.items() if k != "id"}
    return await upsert_record(decision_id, data)


async def upsert_record(
    db: AsyncSurreal,
    record_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    print(f"--- [SurrealDB] upsert_record record_id={record_id} data={data} ---")

    existing = await db.select(record_id)
    print(f"--- [SurrealDB] existing={existing} ---")

    # If SurrealDB returns an error string, treat it as "not found"
    if isinstance(existing, str):
        existing = None

    if existing:
        updated = await db.merge(record_id, data)
        print(f"--- [SurrealDB] updated={updated} ---")

        if isinstance(updated, str):
            raise RuntimeError(updated)

        return updated if updated else {"id": record_id, **data}

    created = await db.create(record_id, data)
    print(f"--- [SurrealDB] created={created} ---")

    if isinstance(created, str):
        raise RuntimeError(created)

    return created if created else {"id": record_id, **data}

async def persist_replan_result(
    disruption_payload: dict | None,
    decision_payload: dict | None,
    relationship_updates: list[dict] | None,
) -> dict:
    async with AsyncSurreal(DB_URL) as db:
        await db.signin({
            "username": os.getenv("SURREAL_USER", "root"),
            "password": os.getenv("SURREAL_PASS", "root"),
        })
        await db.use(os.getenv("SURREAL_NS", "tripweave_ns"), os.getenv("SURREAL_DB", "tripweave_db"))

        saved = {"disruption": None, "decision": None, "relationships_applied": 0}

        # 1. Handle Nodes (Disruption/Decision)
        for key, payload in [("disruption", disruption_payload), ("decision", decision_payload)]:
            if payload and "id" in payload:
                rid = payload.pop("id") # Extract ID to use as the record locator
                # upsert_record is assumed to be a helper using db.upsert(rid, payload)
                saved[key] = await db.upsert(rid, payload)

        # 2. Handle Edges (Relationships)
        if relationship_updates:
            for update in relationship_updates:
                rel = update["relation"]
                src = update["from"]
                dst = update["to"]

                if update["action"] == "create":
                    # RELATE creates a graph edge record
                    await db.query(f"RELATE {src}->{rel}->{dst} SET updated_at = time::now();")
                    saved["relationships_applied"] += 1

                elif update["action"] == "remove":
                    # IMPORTANT: In SurrealDB edges, 'out' is the origin, 'in' is the target
                    await db.query(f"DELETE {rel} WHERE out = {src} AND in = {dst};")
                    saved["relationships_applied"] += 1

        return saved

def serialise_surreal_value(value: Any) -> Any:
    """
    Convert SurrealDB SDK values into plain Python values
    that LangGraph can checkpoint safely.
    """
    if RecordID is not None and isinstance(value, RecordID):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): serialise_surreal_value(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [serialise_surreal_value(item) for item in value]

    if isinstance(value, tuple):
        return [serialise_surreal_value(item) for item in value]

    return value
