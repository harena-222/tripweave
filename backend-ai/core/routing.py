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

def route_after_handler(state: TripWeaveState) -> str:
    next_action = state.get("next_action")

    if next_action in {"create_day_plan_flow", "replan_day_flow", "explain_change_flow"}:
        return "suggest"

    return "persist"
