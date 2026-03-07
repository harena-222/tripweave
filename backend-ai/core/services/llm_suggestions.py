from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


class SuggestionResult(BaseModel):
    suggestions: List[str] = Field(default_factory=list)
    suggested_summary: Optional[str] = None


llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.3,
)

structured_llm = llm.with_structured_output(SuggestionResult)

suggestion_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are TripWeave's itinerary suggestion assistant.

Return concise, practical travel suggestions.
Rules:
- Keep suggestions short.
- Do not invent bookings or hard facts.
- Suggest only plausible alternatives or refinements.
- If context is weak, return fewer suggestions.
- Focus on usefulness, pacing, weather fit, and traveller preference.
""",
        ),
        (
            "human",
            """Mode: {mode}
Destination: {destination}
Date reference: {date_reference}
Interests: {interests}
Walking preference: {walking_preference}
Condition: {condition}
Current summary: {current_summary}

Generate up to 3 useful suggestions and one improved user-facing summary.
""",
        ),
    ]
)

suggestion_chain = suggestion_prompt | structured_llm


async def generate_suggestions(
    *,
    mode: str,
    destination: str,
    date_reference: str,
    interests: list[str],
    walking_preference: str,
    condition: str,
    current_summary: str,
) -> dict:
    result = await suggestion_chain.ainvoke(
        {
            "mode": mode,
            "destination": destination,
            "date_reference": date_reference,
            "interests": ", ".join(interests) if interests else "none",
            "walking_preference": walking_preference,
            "condition": condition,
            "current_summary": current_summary,
        }
    )

    return {
        "alternative_suggestions": result.suggestions,
        "suggested_summary": result.suggested_summary,
    }
