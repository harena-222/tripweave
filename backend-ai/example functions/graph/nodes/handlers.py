from graph.state import TripWeaveState

def handle_create_day_plan(state: TripWeaveState) -> dict:
    # Access the nested dictionary created by the extraction node
    entities = state.get("extracted_entities", {})
    destination = entities.get("destination", "your destination")

    return {
        "final_summary": f"Creating a new day plan for {destination}."
    }


def handle_replan_day(state: TripWeaveState) -> dict:
    entities = state.get("extracted_entities", {})
    # Note: If your LLM doesn't extract 'activity_name', provide a fallback
    activity = entities.get("current_condition") or "the current plan"

    return {
        "final_summary": f"Re-planning the day based on: {activity}."
    }


def handle_move_activity(state: TripWeaveState) -> dict:
    entities = state.get("extracted_entities", {})
    date = entities.get("date_reference", "another time")

    return {
        "final_summary": f"Moving your activity to {date}."
    }


def handle_update_preference(state: TripWeaveState) -> dict:
    entities = state.get("extracted_entities", {})
    # Using 'walking_preference' as an example from your schema
    pref = entities.get("walking_preference", "new preferences")

    return {
        "final_summary": f"Updating your travel style to: {pref}."
    }


def handle_explain_change(state: TripWeaveState) -> dict:
    return {
        "final_summary": "I've analyzed the changes. Here is why the itinerary was adjusted..."
    }
