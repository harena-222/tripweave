from __future__ import annotations

from core.state import TripWeaveState
from core.services.surreal_db import (
    persist_replan_result,
    save_day_plan,
    save_preference_update,
)

async def persist_to_surrealdb(state: TripWeaveState) -> dict:
    if state.get("validation_errors"):
        return {
            "final_summary": "No changes were persisted because validation failed."
        }

    relationships = state.get("relationship_updates", [])

    saved_day_plan = None
    saved_preference = None
    saved_replan = None

    # Persist a new or updated day plan if present
    if state.get("day_plan_payload"):
        saved_day_plan = await save_day_plan(state["day_plan_payload"])

    # Persist a traveller preference update if present
    if state.get("preference_payload"):
        saved_preference = await save_preference_update(state["preference_payload"])

    # Persist disruption / decision / relationships if present
    if (
        state.get("disruption_payload")
        or state.get("decision_payload")
        or relationships
    ):
        saved_replan = await persist_replan_result(
            disruption_payload=state.get("disruption_payload"),
            decision_payload=state.get("decision_payload"),
            relationship_updates=relationships,
        )

    relationships_applied = 0
    if saved_replan:
        relationships_applied = saved_replan.get("relationships_applied", 0)

    saved_parts: list[str] = []

    if saved_day_plan:
        saved_parts.append("day plan")

    if saved_preference:
        saved_parts.append("preference update")

    if state.get("disruption_payload"):
        saved_parts.append("disruption")

    if state.get("decision_payload"):
        saved_parts.append("decision")

    if relationships_applied > 0:
        saved_parts.append("{relationships_applied} relationship updates")

    if not saved_parts:
        saved_parts.append("no durable changes")

    return {
        "final_summary": (
            "{state['final_summary']} "
            "[Persisted: {', '.join(saved_parts)}.]"
        )
    }
