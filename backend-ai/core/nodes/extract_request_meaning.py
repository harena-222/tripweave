from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.domain.intents import TripIntent
from core.state import TripWeaveState

# 🌟 1. New Sub-Schema for Interests
class PreferenceItem(BaseModel):
    name: str = Field(description="The specific interest or activity (e.g., 'scuba diving', 'museums').")
    is_permanent: bool = Field(
        description="True if this is a general personal taste to remember forever. False if it's a one-time request for this trip."
    )

# 2. Updated Main Schema
class TripWeaveExtraction(BaseModel):
    intent: TripIntent = Field(
        description=(
            "The main TripWeave action. "
            "Use create_day_plan for building a new day itinerary, "
            "replan_day for adjusting an existing plan, "
            "move_activity for rescheduling a specific activity, "
            "update_preference for changing user preferences, "
            "and explain_change for explaining a prior decision or modification."
        )
    )
    destination: Optional[str] = None
    date_reference: Optional[str] = None
    # 🌟 Changed from List[str] to List[PreferenceItem]
    interests: List[PreferenceItem] = Field(default_factory=list)
    walking_preference: str = "unspecified"
    current_condition: Optional[str] = None
    urgency: str = "flexible"

# 3. Enhanced System Prompt
system_prompt = """You are an expert travel assistant logic router.
Analyze the user's prompt to extract intent and entities.

CRITICAL RULE FOR INTERESTS:
- Identify if an interest is a PERMANENT personal preference (e.g., "I love extreme sports", "I am a scuba diver")
  or a TEMPORARY trip request (e.g., "I want to see the Eiffel Tower today").
- Set 'is_permanent' to True for lifelong tastes and False for situational requests.
- If a user expresses a preference without a destination, ensure the intent is 'update_preference'.
"""

# Setup the Chain
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0) # Using stable model
structured_llm = llm.with_structured_output(TripWeaveExtraction)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{raw_prompt}")
])

extraction_chain = prompt_template | structured_llm

# 4. Updated Node Function
async def extract_request_meaning(state: TripWeaveState):
    result = await extraction_chain.ainvoke({"raw_prompt": state["raw_prompt"]})

    print(f"--- LLM EXTRACTED: {result.model_dump()} ---")

    intent_map = {
        TripIntent.CREATE_DAY_PLAN: "create_day_plan_flow",
        TripIntent.REPLAN_DAY: "replan_day_flow",
        TripIntent.MOVE_ACTIVITY: "move_activity_flow",
        TripIntent.UPDATE_PREFERENCE: "update_preference_flow",
        TripIntent.EXPLAIN_CHANGE: "explain_change_flow"
    }

    # Map the new PreferenceItem structure back to a dictionary for the state
    extracted_interests = [item.dict() for item in result.interests]

    return {
        "intent": result.intent,
        "next_action": intent_map.get(result.intent, "unknown_flow"),
        "extracted_entities": {
            "destination": result.destination,
            "date_reference": result.date_reference,
            "interests": extracted_interests, # 🌟 Now contains [{'name': '...', 'is_permanent': bool}]
            "walking_preference": result.walking_preference,
            "current_condition": result.current_condition,
            "urgency": result.urgency
        }
    }