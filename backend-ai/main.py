import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.workflow import build_graph
from core.nodes.extract_request_meaning import extract_request_meaning, TripWeaveExtraction
from fastapi.middleware.cors import CORSMiddleware
from surrealdb import AsyncSurreal
import json
import re

def make_record_id(table: str, *parts: str) -> str:
    safe_parts = []

    for part in parts:
        text = str(part).lower()
        text = text.replace(":", "_")
        text = re.sub(r"[^a-z0-9_]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")

        if text:
            safe_parts.append(text)

    return f"{table}:{'_'.join(safe_parts)}"

# 1. Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow your HTML to access the server
    allow_credentials=True,
    allow_methods=["*"], # Allow OPTIONS, POST, GET, etc.
    allow_headers=["*"],
)

# 3. Request model for the API endpoint
class UserRequest(BaseModel):
    raw_prompt: str
    traveller_id: str

class ExtractionData(BaseModel):
    intent: str
    extracted_entities: Dict[str, Any]
    display_type: Optional[str] = None
    final_summary: Optional[str] = None
    final_answer: Optional[str] = None
    alternative_suggestions: List[str] = Field(default_factory=list)
    trip_payload: Optional[Dict[str, Any]] = None
    day_plan_payload: Optional[Dict[str, Any]] = None
    preference_payload: Optional[Dict[str, Any]] = None
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
                "final_answer": final_state.get("final_answer"),
                "alternative_suggestions": final_state.get("alternative_suggestions", []),
                "trip_id": final_state.get("trip_id"),
                "trip_payload": final_state.get("trip_payload"),
                "day_plan_payload": final_state.get("day_plan_payload"),
                "preference_payload": final_state.get("preference_payload"),
                "disruption_payload": final_state.get("disruption_payload"),
                "decision_payload": final_state.get("decision_payload"),
                "relationship_updates": final_state.get("relationship_updates", []),
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

# --- 5. Active Trip Endpoint (추가되는 부분) ---

class ActiveTripRequest(BaseModel):
    traveller_id: str

@app.post("/ai/active-trip")
async def get_active_trip(request: ActiveTripRequest):
    DB_URL = os.getenv("SURREAL_DB_URL", "ws://localhost:8001/rpc")
    SURREAL_USER = os.getenv("SURREAL_USER", "root")
    SURREAL_PASS = os.getenv("SURREAL_PASS", "root")
    SURREAL_NS = os.getenv("SURREAL_NS", "tripweave_ns")
    SURREAL_DB = os.getenv("SURREAL_DB", "tripweave_db")
    try:
        async with AsyncSurreal(DB_URL) as db:
            await db.signin(
            {
                "username": SURREAL_USER,
                "password": SURREAL_PASS,
            })
            await db.use(SURREAL_NS, SURREAL_DB)

            trip_query = """
            SELECT * FROM trip
            WHERE traveller_id = $traveller_id AND status = 'active'
            ORDER BY updated_at DESC LIMIT 1;
            """
            trip_results = await db.query(trip_query, {"traveller_id": request.traveller_id})
            logger.info(f"--- [DEBUG] TRIPS FROM DB: {trip_results} ---")

            if not trip_results:
                return {"status": "error", "message": "No active trip found"}

            active_trip = trip_results[0]
            trip_id = active_trip["id"].id
            logger.info(f"--- [DEBUG] active_trip FROM DB: {active_trip} ---")
            logger.info(f"--- [DEBUG] trip_id FROM DB: {trip_id} ---")

            plan_query = """
            SELECT * FROM day_plan
            WHERE trip_id = $trip_id
            ORDER BY updated_at DESC LIMIT 1;
            """
            plan_results = await db.query(plan_query, {"trip_id": trip_id})
            logger.info(f"--- [DEBUG] PLANS FROM DB: {plan_results} ---") # 🌟 이 로그가 찍히는지 확인!

            final_plan = plan_results[0]["result"][0] if plan_results and plan_results[0].get("result") else {}

            response_data = {
                "status": "success",
                "data": {
                    "display_type": "itinerary_table",
                    "extracted_entities": {
                        "destination": active_trip.get("destination", "London"),
                        "interests": active_trip.get("interests", []) #
                    },
                    "final_summary": final_plan.get("final_summary", f"{active_trip.get('destination')} 여행이 활성화되어 있습니다."),
                    "final_answer": final_plan.get("final_answer", "상세 일정을 불러올 수 없습니다."),
                    "trip_id": str(trip_id)
                }
            }

            logger.info(f"--- ACTIVE TRIP FETCHED ---\n{json.dumps(response_data, indent=2)}")
            return response_data

    except Exception as e:
        logger.error(f"Error fetching active trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
