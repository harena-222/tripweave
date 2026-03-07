from __future__ import annotations

from graph.state import TripWeaveState

async def load_trip_context(state: TripWeaveState):
    traveller_id = state.get("traveller_id")
    print(f"--- LOADING CONTEXT FOR TRAVELLER: {traveller_id} ---")

    # For now, we return an empty dict so we don't overwrite extracted_entities.
    # In the future, you'd fetch the current trip JSON here.
    return {
        "trip_id": "mock_trip_123"
    }
