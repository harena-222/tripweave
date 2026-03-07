# core/nodes/parser.py
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import TripWeaveState

# 1. Restore the full schema to maintain compatibility [cite: 2026-03-07]
class ExtractionSchema(BaseModel):
    intent: str = Field(description="The user's core intent (e.g., create_trip, update_pref)")
    destination: Optional[str] = Field(None, description="The travel destination mentioned")
    date_reference: Optional[str] = Field(None, description="Dates or timeframes mentioned")
    interests: List[str] = Field(default_factory=list, description="List of interests like food or activities")
    walking_preference: str = Field("unspecified", description="Preference for walking vs transport")
    current_condition: Optional[str] = Field(None, description="User's current state (e.g., tired, hungry)")
    urgency: str = Field("flexible", description="How urgent the request is")

# 2. Re-initialize the structured LLM [cite: 2026-03-07]
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)
structured_llm = llm.with_structured_output(ExtractionSchema)

async def parse_meaning(state: TripWeaveState):
    """
    Node 1: Parses raw_prompt using the full schema to ensure no data is lost. [cite: 2026-03-07]
    """
    print(f"--- [Node 1] Parsing: {state['raw_prompt']} ---")

    # Invoke Gemini to get the full structured output [cite: 2026-03-07]
    result = await structured_llm.ainvoke(state["raw_prompt"])

    # Map the results back to your state's extracted_entities [cite: 2026-03-07]
    return {
        "intent": result.intent,
        "extracted_entities": {
            "destination": result.destination,
            "date_reference": result.date_reference,
            "interests": result.interests,
            "walking_preference": result.walking_preference,
            "current_condition": result.current_condition,
            "urgency": result.urgency
        }
    }