from __future__ import annotations

from core.state import TripWeaveState
from core.services.surreal_db import (
    persist_replan_result,
    save_day_plan,
    save_preference_update,
    save_trip,
    persist_relationship_updates
)

async def persist_to_surrealdb(state: TripWeaveState) -> dict:
    print("--- [Persist Node] Running persist_to_surrealdb ---")

    if state.get("validation_errors"):
        return {
            "final_summary": "No changes were persisted because validation failed."
        }

    # 1. Prepare Storage Variables
    relationships = state.get("relationship_updates", []) or []
    saved_trip = None
    saved_day_plan = None
    saved_preference = None
    saved_replan = None

    # 2. Save Core Trip Data
    if state.get("trip_payload"):
        print(f"--- [Persist Node] Saving trip: {state['trip_payload']} ---")
        saved_trip = await save_trip(state["trip_payload"])

    if state.get("day_plan_payload"):
        print(f"--- [Persist Node] Saving day plan: {state['day_plan_payload']} ---")
        saved_day_plan = await save_day_plan(state["day_plan_payload"])

    # 🌟 3. Handle Permanent Preferences (The New Logic)
    # Extract only the interests marked as 'is_permanent' from the state
    entities = state.get("extracted_entities", {}) or {}
    all_interests = entities.get("interests", [])

    # Filter for interests that should be remembered forever
    permanent_interests = [
        item["name"] for item in all_interests
        if isinstance(item, dict) and item.get("is_permanent") is True
    ]

    # If we found permanent ones, or if there's a direct preference_payload, save them
    if permanent_interests or state.get("preference_payload"):
        pref_data = state.get("preference_payload") or {}

        # Merge existing payload with newly discovered permanent interests
        existing_list = pref_data.get("interests", [])
        combined_interests = existing_list.copy()
        for interest in permanent_interests:
            if interest not in combined_interests:
                combined_interests.append(interest)

        payload = {
            "id": state.get("traveller_id"),
            "interests": combined_interests,
            # Add other global fields like walking_preference if needed
            "walking_preference": entities.get("walking_preference")
        }

        print(f"--- [Persist Node] Saving permanent preferences: {payload} ---")
        saved_preference = await save_preference_update(payload)

    # 4. Save Relationships & Decisions
    if (state.get("disruption_payload") or state.get("decision_payload") or relationships):
        print("--- [Persist Node] Saving replan result ---")
        saved_replan = await persist_replan_result(
            disruption_payload=state.get("disruption_payload"),
            decision_payload=state.get("decision_payload"),
            relationship_updates=relationships,
        )

    # 5. Build Final Summary
    final_summary = state.get("suggested_summary") or state.get("final_summary") or "Trip update prepared."
    return {
        "final_answer": final_summary, # Ensuring consistency for the UI
        "final_summary": final_summary
    }