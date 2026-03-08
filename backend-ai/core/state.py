from __future__ import annotations
from typing import Optional, TypedDict, Dict, Any, List
from core.domain.intents import TripIntent

class TripWeaveState(TypedDict):
    raw_prompt: str
    traveller_id: str
    display_type: str

    intent: Optional[TripIntent]
    extracted_entities: Optional[Dict[str, Any]]

    activity_name: Optional[str]
    target_day_phrase: Optional[str]
    condition: Optional[str]
    preference: Optional[str]

    trip_id: Optional[str]
    source_day_plan_id: Optional[str]
    target_day_plan_id: Optional[str]
    activity_id: Optional[str]
    resolved_target_date: Optional[str]

    user_context: Dict[str, Any]
    next_action: Optional[str]

    final_summary: Optional[str]
    final_answer: Optional[str]
    validation_errors: Optional[List[str]]

    alternative_suggestions: Optional[List[str]]
    trip_payload: Optional[Dict[str, Any]]
    day_plan_payload: Optional[Dict[str, Any]]
    preference_payload: Optional[Dict[str, Any]]
    disruption_payload: Optional[Dict[str, Any]]
    suggestion_request: Optional[Dict[str, Any]]
    decision_payload: Optional[Dict[str, Any]]
    relationship_updates: Optional[List[Dict[str, Any]]]
    activities: list[dict]
    activity_payloads: list[dict]
