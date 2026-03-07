from __future__ import annotations

from typing import Any

from core.state import TripWeaveState


def _get_profile(state: TripWeaveState) -> dict[str, Any]:
    user_context = state.get("user_context", {})
    return user_context.get("profile", {}) or {}


def _get_entities(state: TripWeaveState) -> dict[str, Any]:
    return state.get("extracted_entities", {}) or {}


def handle_create_day_plan(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    date_reference = entities.get("date_reference") or "today"
    interests = entities.get("interests", [])
    walking_preference = (
        entities.get("walking_preference")
        or profile.get("walking_preference")
        or "unspecified"
    )

    traveller_id = state.get("traveller_id", "traveller:unknown")
    trip_id = state.get("trip_id", "trip:unknown")
    day_plan_id = "day_plan:{traveller_id.split(':')[-1]}:{date_reference}".replace(" ", "_").lower()

    return {
        "final_summary": "Creating a new day plan for {destination} on {date_reference}.",
        "day_plan_payload": {
            "id": day_plan_id,
            "trip_id": trip_id,
            "traveller_id": traveller_id,
            "destination": destination,
            "date_reference": date_reference,
            "interests": interests,
            "walking_preference": walking_preference,
            "status": "draft",
        },
        "decision_payload": {
            "id": "decision:create_day_plan:{traveller_id.split(':')[-1]}:{date_reference}".replace(" ", "_").lower(),
            "type": "create_day_plan",
            "reason": "User requested a new day plan",
            "summary": "Create a day plan for {destination} on {date_reference}.",
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_day_plan",
                "from": trip_id,
                "to": day_plan_id,
            }
        ],
    }


def handle_replan_day(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    condition = entities.get("current_condition") or "a change in conditions"
    date_reference = entities.get("date_reference") or "today"
    walking_preference = (
        entities.get("walking_preference")
        or profile.get("walking_preference")
        or "unspecified"
    )

    traveller_id = state.get("traveller_id", "traveller:unknown")
    trip_id = state.get("trip_id", "trip:unknown")
    target_day_plan_id = state.get("target_day_plan_id", "day_plan:{traveller_id.split(':')[-1]}:{date_reference}")

    disruption_id = "disruption:{traveller_id.split(':')[-1]}:{date_reference}:{condition}".replace(" ", "_").lower()
    decision_id = "decision:replan:{traveller_id.split(':')[-1]}:{date_reference}".replace(" ", "_").lower()

    return {
        "final_summary": "Re-planning the day based on: {condition}.",
        "disruption_payload": {
            "id": disruption_id,
            "type": "condition_change",
            "condition": condition,
            "date_reference": date_reference,
        },
        "decision_payload": {
            "id": decision_id,
            "type": "replan_day",
            "reason": "{condition} affected the current plan",
            "summary": "Re-plan the day for {date_reference} because of {condition}.",
            "walking_preference_used": walking_preference,
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "affects",
                "from": disruption_id,
                "to": target_day_plan_id,
            },
            {
                "action": "create",
                "relation": "caused_by",
                "from": decision_id,
                "to": disruption_id,
            },
            {
                "action": "create",
                "relation": "modifies",
                "from": decision_id,
                "to": target_day_plan_id,
            },
            {
                "action": "create",
                "relation": "belongs_to",
                "from": decision_id,
                "to": trip_id,
            },
        ],
    }


def handle_move_activity(state: TripWeaveState) -> dict:
    entities = _get_entities(state)

    date_reference = entities.get("date_reference") or "another time"
    activity_id = state.get("activity_id", "activity:unknown")
    source_day_plan_id = state.get("source_day_plan_id", "day_plan:unknown_source")
    target_day_plan_id = state.get("target_day_plan_id", "day_plan:unknown_target")
    traveller_id = state.get("traveller_id", "traveller:unknown")

    decision_id = "decision:move_activity:{traveller_id.split(':')[-1]}:{date_reference}".replace(" ", "_").lower()

    return {
        "final_summary": "Moving your activity to {date_reference}.",
        "decision_payload": {
            "id": decision_id,
            "type": "move_activity",
            "reason": "User requested moving an activity to {date_reference}",
            "summary": "Move activity {activity_id} to {date_reference}.",
        },
        "relationship_updates": [
            {
                "action": "remove",
                "relation": "contains",
                "from": source_day_plan_id,
                "to": activity_id,
            },
            {
                "action": "create",
                "relation": "contains",
                "from": target_day_plan_id,
                "to": activity_id,
            },
            {
                "action": "create",
                "relation": "modifies",
                "from": decision_id,
                "to": activity_id,
            },
        ],
    }


def handle_update_preference(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    traveller_id = state.get("traveller_id", "traveller:unknown")
    new_walking_preference = entities.get("walking_preference", "unspecified")
    old_walking_preference = profile.get("walking_preference", "unknown")

    decision_id = "decision:update_preference:{traveller_id.split(':')[-1]}".replace(" ", "_").lower()

    return {
        "final_summary": "Updating your travel style to: {new_walking_preference}.",
        "preference_payload": {
            "id": traveller_id,
            "walking_preference": new_walking_preference,
        },
        "decision_payload": {
            "id": decision_id,
            "type": "update_preference",
            "reason": "User updated their travel preference",
            "summary": (
                "Walking preference changed from {old_walking_preference} "
                "to {new_walking_preference}."
            ),
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "updated_by",
                "from": traveller_id,
                "to": decision_id,
            }
        ],
    }


def handle_explain_change(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    destination = entities.get("destination") or profile.get("home_destination") or "your trip"

    return {
        "final_summary": (
            "I've analysed the recent changes for {destination}. "
            "Here is why the itinerary was adjusted."
        )
    }
