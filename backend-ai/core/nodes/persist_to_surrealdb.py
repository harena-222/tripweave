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
    print("--- [Persist Node] state keys ---", list(state.keys()))

    if state.get("validation_errors"):
        return {
            "final_summary": "No changes were persisted because validation failed."
        }

    relationships = state.get("relationship_updates", []) or []

    saved_trip = None
    saved_day_plan = None
    saved_preference = None
    saved_replan = None

    if state.get("trip_payload"):
        print(f"--- [Persist Node] Saving trip: {state['trip_payload']} ---")
        saved_trip = await save_trip(state["trip_payload"])
        print(f"--- [Persist Node] saved_trip result: {saved_trip} ---")

    if state.get("day_plan_payload"):
        print(f"--- [Persist Node] Saving day plan: {state['day_plan_payload']} ---")
        saved_day_plan = await save_day_plan(state["day_plan_payload"])
        print(f"--- [Persist Node] saved_day_plan result: {saved_day_plan} ---")

    if state.get("preference_payload"):
        print(f"--- [Persist Node] Saving preference update: {state['preference_payload']} ---")
        saved_preference = await save_preference_update(state["preference_payload"])
        print(f"--- [Persist Node] saved_preference result: {saved_preference} ---")

    if (
        state.get("disruption_payload")
        or state.get("decision_payload")
        or relationships
    ):
        print("--- [Persist Node] Saving replan result ---")
        saved_replan = await persist_replan_result(
            disruption_payload=state.get("disruption_payload"),
            decision_payload=state.get("decision_payload"),
            relationship_updates=relationships,
        )
        print(f"--- [Persist Node] saved_replan result: {saved_replan} ---")

    relationships_applied = 0
    if saved_replan:
        relationships_applied = saved_replan.get("relationships_applied", 0)

    saved_parts: list[str] = []

    if saved_trip:
        saved_parts.append("trip")

    if saved_day_plan:
        saved_parts.append("day plan")

    if saved_preference:
        saved_parts.append("preference update")

    if state.get("disruption_payload"):
        saved_parts.append("disruption")

    if state.get("decision_payload"):
        saved_parts.append("decision")

    if relationships_applied > 0:
        saved_parts.append(f"{relationships_applied} relationship updates")

    if not saved_parts:
        saved_parts.append("no durable changes")

    final_summary = state.get("suggested_summary") or state.get("final_summary") or "Trip update prepared."

    return {
        "final_summary": (
            f"{final_summary} "
            f"[Persisted: {', '.join(saved_parts)}.]"
        )
    }
