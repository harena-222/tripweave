from __future__ import annotations

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
from core.nodes.suggestions import generate_alternative_suggestions
from core.nodes.persist_to_surrealdb import persist_to_surrealdb
from core.nodes.finalise_user_answer import finalise_user_answer
from core.routing import route_by_intent, route_after_handler


def build_graph():
    builder = StateGraph(TripWeaveState)

    builder.add_node("extract_request_meaning", extract_request_meaning)
    builder.add_node("retrieve_memory", retrieve_memory)

    builder.add_node("handle_create_day_plan", handle_create_day_plan)
    builder.add_node("handle_replan_day", handle_replan_day)
    builder.add_node("handle_move_activity", handle_move_activity)
    builder.add_node("handle_update_preference", handle_update_preference)
    builder.add_node("handle_explain_change", handle_explain_change)

    builder.add_node("generate_alternative_suggestions", generate_alternative_suggestions)
    builder.add_node("persist_to_surrealdb", persist_to_surrealdb)
    builder.add_node("finalise_user_answer", finalise_user_answer)

    builder.add_edge(START, "extract_request_meaning")
    builder.add_edge("extract_request_meaning", "retrieve_memory")

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

    builder.add_conditional_edges(
        "handle_create_day_plan",
        route_after_handler,
        {
            "suggest": "generate_alternative_suggestions",
            "persist": "persist_to_surrealdb",
        },
    )
    builder.add_conditional_edges(
        "handle_replan_day",
        route_after_handler,
        {
            "suggest": "generate_alternative_suggestions",
            "persist": "persist_to_surrealdb",
        },
    )
    builder.add_conditional_edges(
        "handle_move_activity",
        route_after_handler,
        {
            "suggest": "generate_alternative_suggestions",
            "persist": "persist_to_surrealdb",
        },
    )
    builder.add_conditional_edges(
        "handle_update_preference",
        route_after_handler,
        {
            "suggest": "generate_alternative_suggestions",
            "persist": "persist_to_surrealdb",
        },
    )
    builder.add_conditional_edges(
        "handle_explain_change",
        route_after_handler,
        {
            "suggest": "generate_alternative_suggestions",
            "persist": "persist_to_surrealdb",
        },
    )

    builder.add_edge("generate_alternative_suggestions", "persist_to_surrealdb")
    builder.add_edge("persist_to_surrealdb", "finalise_user_answer")
    builder.add_edge("finalise_user_answer", END)

    return builder.compile(checkpointer=InMemorySaver())
