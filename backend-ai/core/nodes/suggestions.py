from __future__ import annotations

from core.state import TripWeaveState
from core.services.llm_suggestions import generate_suggestions


async def generate_alternative_suggestions(state: TripWeaveState) -> dict:
    request = state.get("suggestion_request") or {}

    if not request:
        return {}

    suggestions = await generate_suggestions(
        mode=request.get("mode", "general"),
        destination=request.get("destination", "your destination"),
        date_reference=request.get("date_reference", "today"),
        interests=request.get("interests", []),
        walking_preference=request.get("walking_preference", "unspecified"),
        condition=request.get("condition", "none"),
        current_summary=state.get("final_summary", "Trip update prepared."),
    )

    updates = {
        "alternative_suggestions": suggestions.get("alternative_suggestions", []),
    }

    suggested_summary = suggestions.get("suggested_summary")
    if suggested_summary:
        updates["suggested_summary"] = suggested_summary
        updates["final_summary"] = suggested_summary

    return updates
