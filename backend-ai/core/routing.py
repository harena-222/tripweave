from core.domain.intents import TripIntent
from core.state import TripWeaveState


def route_by_intent(state: TripWeaveState) -> str:
    intent = state.get("intent")
    print(f"--- ROUTER: Received intent '{intent}' ---")

    if intent == TripIntent.CREATE_DAY_PLAN:
        return "create"
    if intent == TripIntent.REPLAN_DAY:
        return "replan"
    if intent == TripIntent.MOVE_ACTIVITY:
        return "move"
    if intent == TripIntent.UPDATE_PREFERENCE:
        return "update_pref"
    if intent == TripIntent.EXPLAIN_CHANGE:
        return "explain"

    print(f"--- ROUTER WARNING: Intent '{intent}' not recognized, falling back to explain ---")
    return "explain"
