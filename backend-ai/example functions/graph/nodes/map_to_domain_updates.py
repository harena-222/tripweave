from __future__ import annotations
from graph.state import TripWeaveState

def map_to_domain_updates(state: TripWeaveState) -> dict:
    # Use .get to avoid KeyErrors during the demo
    activity_id = state.get("activity_id", "act_unknown")
    source_id = state.get("source_day_plan_id", "day_01")
    target_id = state.get("target_day_plan_id", "day_02")
    condition = state.get("condition", "weather_change")

    # Hardcoded for the hackathon MVP logic
    disruption_id = f"disruption:{condition}"
    decision_id = f"decision:{state.get('traveller_id', 'user')}_move"

    return {
        "domain_updates": {  # Wrapping this in a key makes it easier to track in State
            "disruption_payload": {
                "id": disruption_id,
                "type": "context_shift",
                "condition": condition,
            },
            "relationship_updates": [
                # 1. Unlink from old day
                {"action": "remove", "relation": "contains", "from": source_id, "to": activity_id},
                # 2. Link to new day
                {"action": "create", "relation": "contains", "from": target_id, "to": activity_id},
                # 3. Audit trail (Why did this move?)
                {"action": "create", "relation": "caused_by", "from": activity_id, "to": decision_id},
            ],
        }
    }
