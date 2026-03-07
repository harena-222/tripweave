import os
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