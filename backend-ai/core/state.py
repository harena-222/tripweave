from typing import TypedDict, List, Optional

class TripWeaveState(TypedDict):
    # The original user input string
    raw_prompt: str
    # Unique ID for the user (e.g., 'traveller:moon_inzoo')
    traveller_id: str

    # Parsed intent from Node 1 (e.g., 'create_trip')
    intent: str
    # Extracted entities like destination or dates
    extracted_entities: dict

    # Collected context from SurrealDB, Weather API, etc.
    user_context: dict

    # The final natural language response from the AI
    final_answer: str