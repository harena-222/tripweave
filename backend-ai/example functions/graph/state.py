from __future__ import annotations
from typing import Optional, TypedDict, Dict, Any, List
from domain.intents import TripIntent


class TripWeaveState(TypedDict):
    raw_prompt: str
    intent: Optional[TripIntent]
    # ADD THIS LINE:
    extracted_entities: Optional[Dict[str, Any]]

    # Keep your existing fields
    activity_name: Optional[str]
    target_day_phrase: Optional[str]
    condition: Optional[str]
    preference: Optional[str]
    traveller_id: Optional[str]
    trip_id: Optional[str]
    final_summary: Optional[str]
    validation_errors: Optional[list[str]]
    # If you are using next_action in your API, add it here too
    next_action: Optional[str]
    disruption_payload: Optional[Dict[str, Any]]
    decision_payload: Optional[Dict[str, Any]]
    relationship_updates: Optional[List[Dict[str, Any]]]
