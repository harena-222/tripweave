from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from core.state import TripWeaveState
from core.nodes.extract_request_meaning import extract_request_meaning
from core.nodes.retrievals.memory import retrieve_memory
from core.nodes.handlers import (
    handle_create_day_plan,
    handle_replan_day,
    handle_move_activity,
    handle_update_preference,
    handle_explain_change,
)
from core.routing import route_by_intent


def build_graph():
    builder = StateGraph(TripWeaveState)

    # 1. Register all nodes
    builder.add_node("extract_request_meaning", extract_request_meaning)
    builder.add_node("retrieve_memory", retrieve_memory)

    builder.add_node("handle_create_day_plan", handle_create_day_plan)
    builder.add_node("handle_replan_day", handle_replan_day)
    builder.add_node("handle_move_activity", handle_move_activity)
    builder.add_node("handle_update_preference", handle_update_preference)
    builder.add_node("handle_explain_change", handle_explain_change)

    # 2. Define the entry flow
    builder.add_edge(START, "extract_request_meaning")
    builder.add_edge("extract_request_meaning", "retrieve_memory")

    # 3. Branch by intent after memory has been loaded
    builder.add_conditional_edges(
        "retrieve_memory",
        route_by_intent,
        {
            "create": "handle_create_day_plan",
            "replan": "handle_replan_day",
            "move": "handle_move_activity",
            "update_pref": "handle_update_preference",
            "explain": "handle_explain_change",
        },
    )

    # 4. All handlers go to END
    builder.add_edge("handle_create_day_plan", END)
    builder.add_edge("handle_replan_day", END)
    builder.add_edge("handle_move_activity", END)
    builder.add_edge("handle_update_preference", END)
    builder.add_edge("handle_explain_change", END)

    return builder.compile(checkpointer=InMemorySaver())
