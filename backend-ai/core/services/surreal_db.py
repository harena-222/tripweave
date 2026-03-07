import os
from typing import Any
from surrealdb import AsyncSurreal

# Create a global connection string from .env [cite: 2026-03-07]
DB_URL = os.getenv("SURREAL_DB_URL", "ws://localhost:8001/rpc")

async def get_user_profile(traveller_id: str):
    """
    Connects to SurrealDB and fetches the profile for the specific traveller. [cite: 2026-03-07]
    """
    async with AsyncSurreal(DB_URL) as db:
        # 1. Sign in with credentials from .env [cite: 2026-03-07]
        await db.signin({
            "username": os.getenv("SURREAL_USER", "root"),
            "password": os.getenv("SURREAL_PASS", "root")
        })

        # 2. Select the Namespace and Database [cite: 2026-03-07]
        await db.use(os.getenv("SURREAL_NS", "tripweave_ns"), os.getenv("SURREAL_DB", "tripweave_db"))

        # 3. Select the traveller record [cite: 2026-03-07]
        # Example traveller_id: "traveller:idiots"
        profile = await db.select(traveller_id)
        print(f"--- [SurrealDB] Successfully fetched: {profile} ---")

        return profile if profile else {"message": "Profile not found"}

async def save_day_plan(day_plan_payload: dict) -> dict:
    day_plan_id = day_plan_payload["id"]
    data = {k: v for k, v in day_plan_payload.items() if k != "id"}
    return await upsert_record(day_plan_id, data)


async def save_preference_update(preference_payload: dict) -> dict:
    traveller_id = preference_payload["id"]
    data = {k: v for k, v in preference_payload.items() if k != "id"}
    return await upsert_record(traveller_id, data)


async def upsert_record(
    db: AsyncSurreal,
    record_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a record if it does not exist, otherwise merge the new data into it.

    Parameters
    ----------
    db:
        An active SurrealDB client connection.
    record_id:
        The full record ID, for example "traveller:idiots".
    data:
        The fields to store on the record.

    Returns
    -------
    dict[str, Any]
        The created or updated record data.
    """
    existing = await db.select(record_id)

    if existing:
        updated = await db.merge(record_id, data)
        return updated if updated else {"id": record_id, **data}

    created = await db.create(record_id, data)
    return created if created else {"id": record_id, **data}
