from __future__ import annotations

from tripweave.graph.state import TripWeaveState


def persist_to_surrealdb(state: TripWeaveState) -> dict:
    if state.get("validation_errors"):
        return {
            "final_summary": "No changes were persisted because validation failed."
        }

    return {
        "final_summary": (
            f"{state['final_summary']} "
            "[Stub persistence only: no database writes yet.]"
        )
    }