from __future__ import annotations

from core.state import TripWeaveState

def collect_validation_errors(state: TripWeaveState) -> list[str]:
    """
    Check whether the minimum required data for re-planning exists.
    """
    errors: list[str] = []

    if not state.get("trip_id"):
        errors.append("Missing trip context.")

    if not state.get("traveller_id"):
        errors.append("Missing traveller context.")

    if not state.get("target_day_plan_id"):
        errors.append("Missing target day plan.")

    return errors

def build_replan_summary(state: TripWeaveState) -> str:
    """
    Build a safe final summary from validated state.
    """
    entities = state.get("extracted_entities", {}) or {}

    activity_name = (
        state.get("activity_name")
        or entities.get("activity_name")
        or "The activity"
    )

    resolved_target_date = (
        state.get("resolved_target_date")
        or entities.get("date_reference")
        or "the target day"
    )

    condition = (
        state.get("condition")
        or entities.get("current_condition")
        or "current conditions"
    )

    return (
        f"{activity_name} will be moved to {resolved_target_date} because "
        f"{condition} affects the current plan."
    )

def validate_and_replan(state: TripWeaveState) -> dict:
    """
    Validate the state before persistence and prepare a final summary.
    """
    errors = collect_validation_errors(state)

    if errors:
        return {
            "validation_errors": errors,
            "final_summary": "Validation failed. No itinerary changes prepared.",
        }

    final_summary = build_replan_summary(state)

    return {
        "validation_errors": [],
        "final_summary": final_summary,
    }
