import os
from typing import List, Optional
from typing import TypedDict
from typing import Dict, Any
from domain.intents import TripIntent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from graph.workflow import build_graph
from graph.nodes.extract_request_meaning import extract_request_meaning, TripWeaveExtraction
import json

# 1. Initialize FastAPI app
app = FastAPI()

# 3. Request model for the API endpoint
class UserRequest(BaseModel):
    raw_prompt: str
    traveller_id: str

class ExtractionData(BaseModel):
    intent: str
    extracted_entities: Dict[str, Any]
    final_summary: Optional[str] = None
    disruption_payload: Optional[Dict[str, Any]] = None
    decision_payload: Optional[Dict[str, Any]] = None
    relationship_updates: List[Dict[str, Any]] = Field(default_factory=list)

class ProcessResponse(BaseModel):
    status: str
    data: ExtractionData
    next_action: str

app_workflow = build_graph()

# 4. API Endpoints
import logging

# Configure logging to see the state in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/ai/process", response_model=ProcessResponse)
async def process_meaning(request: UserRequest):
    try:
        inputs = {"raw_prompt": request.raw_prompt, "traveller_id": request.traveller_id}
        config = {"configurable": {"thread_id": request.traveller_id}}

        final_state = await app_workflow.ainvoke(inputs, config=config)

        # LOG THE RESPONSE
        logger.info(f"Final State for {request.traveller_id}: {final_state}")

        response_data = {
            "status": "success",
            "data": {
                "intent": final_state.get("intent", "unknown"),
                "extracted_entities": final_state.get("extracted_entities", {}),
                "final_summary": final_state.get("final_summary"),
                "disruption_payload": final_state.get("disruption_payload"),
                "decision_payload": final_state.get("decision_payload"),
                "relationship_updates": final_state.get("relationship_updates", [])
            },
            "next_action": final_state.get("next_action", "unknown_flow"),
        }

        # 2. Log the outgoing response for debugging
        # Using json.dumps ensures the log is easy to read in your terminal
        logger.info(f"--- OUTGOING API RESPONSE ---\n{json.dumps(response_data, indent=2)}")

        # 3. Return the response
        return response_data

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Processing Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
