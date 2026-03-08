from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import TripWeaveState

class FinalAnswerResult(BaseModel):
    final_answer: str = Field(
        description="The main text response for the user. Use Markdown tables for itineraries or bullet points for lists."
    )
    display_type: str = Field(
        description="UI hint for the frontend: 'itinerary_table' (full plans), 'recommendation_list' (places/food), 'alert' (changes), or 'text_only' (chat)."
    )

# Use a stable model for structured output
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.2,
)

structured_llm = llm.with_structured_output(FinalAnswerResult)

final_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are TripWeave's intelligent travel coordinator.
Your task is to wrap up the workflow result into a polished, UI-ready response.

--- UI RENDERING RULES ---
1. FULL ITINERARY (e.g., CREATE_DAY_PLAN):
   - Format: Use a Markdown table with columns: | Time | Activity | Description |.
   - Set display_type: 'itinerary_table'.

2. RECOMMENDATIONS (e.g., Nearby Restaurants, Attractions):
   - Format: Use a bold list like **[Place Name]** (Rating/Distance) - Brief tip.
   - Set display_type: 'recommendation_list'.

3. CHANGES/REPLAN (e.g., Weather issues, Replanning):
   - Format: Highlight what changed (Before vs. After) and why.
   - Set display_type: 'alert'.

4. GENERAL CHAT:
   - Format: Natural conversational text.
   - Set display_type: 'text_only'.

--- GENERAL RULES ---
- Keep the introduction short (1-2 sentences).
- Be helpful and friendly.
- Do NOT mention internal IDs, database terms, or graph nodes.
""",
        ),
        (
            "human",
            """
Intent: {intent}
Destination: {destination}
Final Summary: {final_summary}

--- CONTEXT DATA ---
Activities/Places: {activities_data}
Disruption Info: {disruption}
---
""",
        ),
    ]
)

final_answer_chain = final_answer_prompt | structured_llm

async def finalise_user_answer(state: TripWeaveState) -> dict:
    """Finalizes the response with a specific display type for the frontend UI."""

    entities = state.get("extracted_entities", {}) or {}

    # Prepare structured data for the LLM to decide the format
    activities = state.get("activity_payloads", [])
    activities_str = ""
    if activities:
        # Formatting data points to help the LLM see the details clearly
        activities_str = "\n".join([
            f"- {a.get('start_time', 'N/A')}: {a.get('place_name')} ({a.get('description', '')})"
            for a in activities
        ])

    disruption = state.get("disruption_payload") or "No major disruptions."

    # Invoke the structured LLM chain
    result = await final_answer_chain.ainvoke(
        {
            "intent": getattr(state.get("intent"), "value", state.get("intent", "unknown")),
            "destination": entities.get("destination") or "the destination",
            "final_summary": state.get("final_summary", "Updates are ready."),
            "activities_data": activities_str if activities_str else "No specific places/activities provided.",
            "disruption": disruption,
        }
    )

    # Return both the final text and the UI hint
    return {
        "final_answer": result.final_answer,
        "display_type": result.display_type
    }