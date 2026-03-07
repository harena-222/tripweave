import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from enum import Enum

# 1. Initialize FastAPI app
app = FastAPI()

class TripIntent(str, Enum):
    CREATE_DAY_PLAN = "create_day_plan"
    REPLAN_DAY = "replan_day"
    MOVE_ACTIVITY = "move_activity"
    UPDATE_PREFERENCE = "update_preference"
    EXPLAIN_CHANGE = "explain_change"

# 2. Define the Pydantic schema (Your logic)
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
# 3. Request model for the API endpoint
class UserRequest(BaseModel):
    raw_prompt: str
    traveller_id: str

# 4. Set up the LLM (Ensure GOOGLE_API_KEY is in your environment)
# You can also set it manually: os.environ["GOOGLE_API_KEY"] = "YOUR_KEY"
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0
)

structured_llm = llm.with_structured_output(TripWeaveExtraction)

system_prompt = """
You are an expert travel assistant logic router for TripWeave.

Your job is to analyse the user's input and extract structured meaning.

Intent must be exactly one of:
- create_day_plan
- replan_day
- move_activity
- update_preference
- explain_change

Rules:
- Do not invent new intent names.
- Pick the closest matching intent from the allowed list.
- Do not make up information.
- If a field is not mentioned, leave it empty or use the default.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{raw_prompt}")
])

extraction_chain = prompt_template | structured_llm

async def extract_meaning(raw_prompt: str) -> dict:
    result = extraction_chain.invoke({"raw_prompt": raw_prompt})

    return {
        "intent": result.intent.value,
        "extracted_entities": {
            "destination": result.destination,
            "date_reference": result.date_reference,
            "interests": result.interests,
            "walking_preference": result.walking_preference,
            "current_condition": result.current_condition,
            "urgency": result.urgency,
        },
    }

# 5. The API Endpoint that Node.js calls
@app.post("/ai/process")
async def process_meaning(request: UserRequest):
    try:
        print(f"--- Node 1: Extracting Meaning for: '{request.raw_prompt}' ---")

        data = await extract_meaning(request.raw_prompt)

        print(f"--- Node 1: result: '{data}' ---")

        return {
            "status": "success",
            "data": data,
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)