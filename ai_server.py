import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Initialize FastAPI app
app = FastAPI()

# 2. Define the Pydantic schema (Your logic)
class TripWeaveExtraction(BaseModel):
    intent: str = Field(description="The user's core intent.")
    destination: Optional[str] = None
    date_reference: Optional[str] = None
    interests: Optional[List[str]] = []
    walking_preference: Optional[str] = "unspecified"
    current_condition: Optional[str] = None
    urgency: Optional[str] = "flexible"

# 3. Request model for the API endpoint
class UserRequest(BaseModel):
    raw_prompt: str
    traveller_id: str

# 4. Set up the LLM (Ensure GOOGLE_API_KEY is in your environment)
# You can also set it manually: os.environ["GOOGLE_API_KEY"] = "YOUR_KEY"
llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
structured_llm = llm.with_structured_output(TripWeaveExtraction)

system_prompt = """You are an expert travel assistant logic router for TripWeave.
Analyze the user's input and extract the specific entities and intent.
Do not make up information. If a field is not mentioned in the prompt, leave it empty or use the default."""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{raw_prompt}")
])

extraction_chain = prompt_template | structured_llm

# 5. The API Endpoint that Node.js calls
@app.post("/ai/process")
async def process_meaning(request: UserRequest):
    try:
        print(f"--- Node 1: Extracting Meaning for: '{request.raw_prompt}' ---")

        # Run the LangChain logic
        result = extraction_chain.invoke({"raw_prompt": request.raw_prompt})
        print(f"--- Node 1: result: '{result}' ---")

        # Return the data in the format your Node.js expects
        return {
            "status": "success",
            "data": {
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
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)