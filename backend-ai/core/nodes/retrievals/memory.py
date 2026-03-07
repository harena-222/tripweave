from core.state import TripWeaveState
from core.services.surreal_db import get_user_profile

async def retrieve_memory(state: TripWeaveState):
    """
    Node 2-A: Retrieves historical data and preferences for the specific traveller.
    """
    print(f"--- [Node 2-A] Fetching memory for: {state['traveller_id']} ---")

    # Fetch from SurrealDB service
    profile = await get_user_profile(state["traveller_id"])

    # Merge with existing user_context in State
    return {
        "user_context": {
            "profile": profile
        }
    }