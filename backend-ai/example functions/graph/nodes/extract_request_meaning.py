from typing import Optional, List
from typing_extensions import TypedDict  # Or from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from domain.intents import TripIntent
from graph.state import TripWeaveState

# 1. Define the Schema (Specific to this node)
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
    interests: List[str] = Field(default_factory=list)
    walking_preference: str = "unspecified"
    current_condition: Optional[str] = None
    urgency: str = "flexible"

# 2. Setup the Chain
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)
structured_llm = llm.with_structured_output(TripWeaveExtraction)

system_prompt = "You are an expert travel assistant logic router..."
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{raw_prompt}")
])

extraction_chain = prompt_template | structured_llm

# 3. The Node Function
async def extract_request_meaning(state: TripWeaveState):
    # 1. Run the LLM
    result = await extraction_chain.ainvoke({"raw_prompt": state["raw_prompt"]})

    # DEBUG: Check your terminal! If this prints empty, the LLM is the issue.
    print(f"--- LLM EXTRACTED: {result.model_dump()} ---")

    # 2. Map Intent to Flow
    # Since TripIntent is a str-enum, result.intent is already "create_day_plan"
    intent_map = {
        TripIntent.CREATE_DAY_PLAN: "create_day_plan_flow",
        TripIntent.REPLAN_DAY: "replan_day_flow",
        TripIntent.MOVE_ACTIVITY: "move_activity_flow",
        TripIntent.UPDATE_PREFERENCE: "update_preference_flow",
        TripIntent.EXPLAIN_CHANGE: "explain_change_flow"
    }

    # 3. Construct the exact dictionary for the state
    return {
        "intent": result.intent,
        "next_action": intent_map.get(result.intent, "unknown_flow"),
        "extracted_entities": {
            "destination": result.destination,
            "date_reference": result.date_reference,
            "interests": result.interests,
            "walking_preference": result.walking_preference,
            "current_condition": result.current_condition,
            "urgency": result.urgency
        }
    }
