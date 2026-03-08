from __future__ import annotations

from typing import Any

from core.state import TripWeaveState

def make_record_id(table: str, *parts: str) -> str:
    safe_parts = [
        str(part).replace(" ", "_").replace(":", "_").lower()
        for part in parts
    ]
    return f"{table}:{'_'.join(safe_parts)}"

def _get_profile(state: TripWeaveState) -> dict[str, Any]:
    user_context = state.get("user_context", {}) or {}
    profile = user_context.get("profile")

    if isinstance(profile, list):
        return profile[0] if profile else {}

    if isinstance(profile, dict):
        return profile

    return {}


def _get_entities(state: TripWeaveState) -> dict[str, Any]:
    entities = state.get("extracted_entities", {})
    return entities if isinstance(entities, dict) else {}


def handle_create_day_plan(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    date_reference = entities.get("date_reference") or "today"
    interests_list = [item['name'] for item in entities.get("interests", [])]
    interests = f"{', '.join(interests_list)}"


    walking_preference = (
        entities.get("walking_preference")
        or profile.get("walking_preference")
        or "unspecified"
    )

    traveller_id = state.get("traveller_id", "traveller:unknown")
    traveller_slug = traveller_id.split(":")[-1]

    trip_id = state.get("trip_id")
    trip_id = make_record_id("trip", traveller_slug, destination, "active")

    day_plan_id = make_record_id("day_plan", traveller_slug, date_reference)
    decision_id = make_record_id("decision", "create_day_plan", traveller_slug, date_reference)

    trip_payload = {
        "id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "status": "active",
    }

    day_plan_payload = {
        "id": day_plan_id,
        "trip_id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "date_reference": date_reference,
        "interests": interests,
        "walking_preference": walking_preference,
        "status": "draft",
    }

    return {
        "next_action": "create_day_plan_flow",
        "trip_id": trip_id,
        "final_summary": (
            f"I've started a draft day plan for {destination} on {date_reference}, "
            f"shaped around {', '.join(interests) if interests else 'your preferences'}."
        ),
        "trip_payload": trip_payload,
        "day_plan_payload": day_plan_payload,
        "decision_payload": {
            "id": decision_id,
            "type": "create_day_plan",
            "reason": "User requested a new day plan",
            "summary": f"Create a day plan for {destination} on {date_reference}.",
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_trip",
                "from": traveller_id,
                "to": trip_id,
            },
            {
                "action": "create",
                "relation": "has_day_plan",
                "from": trip_id,
                "to": day_plan_id,
            },
        ],
        "suggestion_request": {
            "mode": "create_day_plan",
            "destination": destination,
            "date_reference": date_reference,
            "interests": interests,
            "walking_preference": walking_preference,
            "condition": "none",
        },
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
    traveller_slug = traveller_id.split(":")[-1]

    trip_id = state.get("trip_id")
    if not trip_id:
        destination = entities.get("destination") or profile.get("home_destination") or "trip"
        trip_id = make_record_id("trip", traveller_slug, destination, "active")

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    target_day_plan_id = state.get(
        "target_day_plan_id",
        make_record_id("day_plan", traveller_slug, date_reference),
    )

    disruption_id = make_record_id("disruption", traveller_slug, date_reference, condition)
    decision_id = make_record_id("decision", "replan", traveller_slug, date_reference)

    trip_payload = {
        "id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "status": "active",
    }

    return {
        "next_action": "replan_day_flow",
        "trip_id": trip_id,
        "final_summary": (
            f"I've adjusted the {date_reference} plan for {destination} because of {condition}, "
            f"while keeping your walking preference in mind."
        ),
        "trip_payload": trip_payload,
        "disruption_payload": {
            "id": disruption_id,
            "type": "condition_change",
            "condition": condition,
            "date_reference": date_reference,
        },
        "decision_payload": {
            "id": decision_id,
            "type": "replan_day",
            "reason": f"{condition} affected the current plan",
            "summary": f"Re-plan the day for {date_reference} because of {condition}.",
            "walking_preference_used": walking_preference,
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_trip",
                "from": traveller_id,
                "to": trip_id,
            },
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
        "suggestion_request": {
            "mode": "replan_day",
            "destination": destination,
            "date_reference": date_reference,
            "interests": entities.get("interests", []),
            "walking_preference": walking_preference,
            "condition": condition,
        },
    }


def handle_move_activity(state: TripWeaveState) -> dict:
    entities = _get_entities(state)
    profile = _get_profile(state)

    date_reference = entities.get("date_reference") or "another time"
    activity_id = state.get("activity_id", "activity:unknown")
    source_day_plan_id = state.get("source_day_plan_id", "day_plan:unknown_source")
    target_day_plan_id = state.get("target_day_plan_id", "day_plan:unknown_target")
    traveller_id = state.get("traveller_id", "traveller:unknown")
    traveller_slug = traveller_id.split(":")[-1]

    trip_id = state.get("trip_id")
    if not trip_id:
        destination = entities.get("destination") or profile.get("home_destination") or "trip"
        trip_id = make_record_id("trip", traveller_slug, destination, "active")

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    decision_id = make_record_id("decision", "move_activity", traveller_slug, date_reference)

    trip_payload = {
        "id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "status": "active",
    }

    return {
        "next_action": "move_activity_flow",
        "trip_id": trip_id,
        "final_summary": (
            f"I've moved the activity to {date_reference} and updated the plan structure."
        ),
        "trip_payload": trip_payload,
        "decision_payload": {
            "id": decision_id,
            "type": "move_activity",
            "reason": f"User requested moving an activity to {date_reference}",
            "summary": f"Move activity {activity_id} to {date_reference}.",
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_trip",
                "from": traveller_id,
                "to": trip_id,
            },
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
            {
                "action": "create",
                "relation": "belongs_to",
                "from": decision_id,
                "to": trip_id,
            },
        ],
    }


def handle_update_preference(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    extracted = state.get("extracted_entities", {})
    interests_list = [item['name'] for item in extracted.get("interests", [])]
    traveller_id = state.get("traveller_id", "traveller:unknown")
    traveller_slug = traveller_id.split(":")[-1]

    trip_id = state.get("trip_id")
    if not trip_id:
        destination = entities.get("destination") or profile.get("home_destination") or "trip"
        trip_id = make_record_id("trip", traveller_slug, destination, "active")

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    new_walking_preference = entities.get("walking_preference", "unspecified")
    old_walking_preference = profile.get("walking_preference", "unknown")

    decision_id = make_record_id("decision", "update_preference", traveller_slug)

    trip_payload = {
        "id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "status": "active",
    }

    return {
        "next_action": "update_preference_flow",
        "trip_id": trip_id,
        "final_summary": (
            f"I've updated your walking preference from {old_walking_preference} "
            f"to {new_walking_preference} for future planning."
        ),
        "trip_payload": trip_payload,
        "preference_payload": {
            "id": state.get("traveller_id"),
            "interests": extracted.get("interests", []),
            "walking_preference": extracted.get("walking_preference", "unspecified"),
            "urgency": extracted.get("urgency", "flexible")
        },
        "decision_payload": {
            "id": decision_id,
            "type": "update_preference",
            "reason": "User updated personal travel preferences",
            "summary": (
                f"Updated interests with: {', '.join(interests_list)}. "
                f"Walking preference is now {new_walking_preference}."
            ),
        },
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_trip",
                "from": traveller_id,
                "to": trip_id,
            },
            {
                "action": "create",
                "relation": "updated_by",
                "from": traveller_id,
                "to": decision_id,
            },
            {
                "action": "create",
                "relation": "belongs_to",
                "from": decision_id,
                "to": trip_id,
            },
        ],
    }


def handle_explain_change(state: TripWeaveState) -> dict:
    profile = _get_profile(state)
    entities = _get_entities(state)

    traveller_id = state.get("traveller_id", "traveller:unknown")
    traveller_slug = traveller_id.split(":")[-1]

    trip_id = state.get("trip_id")
    if not trip_id:
        destination_seed = entities.get("destination") or profile.get("home_destination") or "trip"
        trip_id = make_record_id("trip", traveller_slug, destination_seed, "active")

    destination = entities.get("destination") or profile.get("home_destination") or "your destination"
    trip_payload = {
        "id": trip_id,
        "traveller_id": traveller_id,
        "destination": destination,
        "status": "active",
    }

    return {
        "next_action": "explain_change_flow",
        "trip_id": trip_id,
        "trip_payload": trip_payload,
        "final_summary": (
            f"I've reviewed the recent planning changes for {destination} and prepared "
            f"a clear explanation of what changed and why."
        ),
        "relationship_updates": [
            {
                "action": "create",
                "relation": "has_trip",
                "from": traveller_id,
                "to": trip_id,
            }
        ],
        "suggestion_request": {
            "mode": "explain_change",
            "destination": destination,
            "date_reference": entities.get("date_reference") or "current plan",
            "interests": entities.get("interests", []),
            "walking_preference": entities.get("walking_preference")
            or profile.get("walking_preference")
            or "unspecified",
            "condition": entities.get("current_condition") or "recent changes",
        },
    }
