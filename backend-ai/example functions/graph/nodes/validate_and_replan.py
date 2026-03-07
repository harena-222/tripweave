from __future__ import annotations

from tripweave.graph.state import TripWeaveState


def validate_and_replan(state: TripWeaveState) -> dict:
    errors: list[str] = []

    if not state.get("trip_id"):
        errors.append("Missing trip context.")

    if not state.get("activity_id"):
        errors.append("Missing activity resolution.")

    if not state.get("target_day_plan_id"):
        errors.append("Missing target day plan.")

    if errors:
        return {
            "validation_errors": errors,
            "final_summary": "Validation failed. No itinerary changes prepared.",
        }

    activity_name = state.get("activity_name", "The activity")
    resolved_target_date = state.get("resolved_target_date", "the target day")
    condition = state.get("condition", "current conditions")

    return {
        "validation_errors": [],
        "final_summary": (
            f"{activity_name} will be moved to {resolved_target_date} because {condition} "
            "affects the current plan."
        ),
    }