import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.graph import compiled_graph

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="TripWeave AI Backend")

# 1. Define the Request Body (Matching what Node.js sends)
class UserRequest(BaseModel):
    raw_prompt: str
    traveller_id: str

# 2. Health Check (To see if the server is alive)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gemini-3.1-flash-lite"}

# 3. The Main AI Endpoint
@app.post("/ai/process")
async def process_meaning(request: UserRequest):
    try:
        print(f"--- 🚀 Starting Graph for Traveller: {request.traveller_id} ---")

        # Initial State to feed into LangGraph
        initial_state = {
            "raw_prompt": request.raw_prompt,
            "traveller_id": request.traveller_id,
            "intent": "",
            "extracted_entities": {},
            "user_context": {},
            "final_answer": ""
        }

        # Run the LangGraph (Asynchronously)
        # .ainvoke() starts the flow from Node 1
        result = await compiled_graph.ainvoke(initial_state)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        print(f"❌ Error in AI Processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run the server on Port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)