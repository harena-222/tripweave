from __future__ import annotations

from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Data Models for Structured Output ---

class ActivityInfo(BaseModel):
    """Represents a single travel activity/event."""
    place_name: str = Field(description="The clear name of the venue or landmark (e.g., 'Borough Market').")
    start_time: str = Field(description="The scheduled start time in 24-hour format (e.g., '09:00', '14:30').")
    duration_mins: int = Field(description="Estimated duration of stay at this location in minutes (e.g., 120).")
    description: str = Field(description="A short 1-2 sentence explanation of what to do here and why it's recommended.")

class SuggestionResult(BaseModel):
    """The final structured response from the LLM."""
    activities: List[ActivityInfo] = Field(
        default_factory=list,
        description="A list of recommended activities sorted in chronological order."
    )
    suggested_summary: Optional[str] = Field(
        None,
        description="A natural, friendly summary of the overall trip plan."
    )

# --- 2. LLM Configuration ---

# Using Gemini for speed and cost-efficiency
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.3,
)

structured_llm = llm.with_structured_output(SuggestionResult)

# --- 3. Prompt Engineering ---

suggestion_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are TripWeave's itinerary suggestion assistant.

Return concise, practical travel suggestions in a structured format.
Rules:
- Personalization: Prioritize activities that match the 'Interests' provided.
- Realism: Ensure start times and durations make sense for a single day.
- Tone: Be helpful and encouraging, like a local expert.
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

Generate up to 3 structured activities and one improved user-facing summary based on the traveller's profile and current context.
""",
        ),
    ]
)

suggestion_chain = suggestion_prompt | structured_llm

# --- 4. Node Logic with Context Injection ---

def _normalise_profile(user_context: dict) -> dict:
    if not user_context:
        return {}

    profile = user_context.get("profile")

    if isinstance(profile, list):
        first = profile[0] if profile else {}
        return first if isinstance(first, dict) else {}

    if isinstance(profile, dict):
        return profile

    return {}

def _extract_interest_names(items) -> list[str]:
    if not isinstance(items, list):
        return []

    names: list[str] = []

    for item in items:
        if isinstance(item, dict) and "name" in item and isinstance(item["name"], str):
            names.append(item["name"])
        elif isinstance(item, str):
            names.append(item)

    return names

async def generate_suggestions(
    *,
    mode: str,
    destination: str,
    date_reference: str,
    interests: list[Union[dict, str]], # Supports both simple strings and structured PreferenceItems
    walking_preference: str,
    condition: str,
    current_summary: str,
    user_context: Optional[dict] = None, # User profile data fetched from SurrealDB
) -> dict:
    """
    Generates personalized travel suggestions by merging current input with
    permanent user preferences stored in the database.
    """

    profile = _normalise_profile(user_context)

    print("--- [Suggestions] raw user_context ---", user_context)
    print("--- [Suggestions] normalised profile ---", profile)

    permanent_interests = _extract_interest_names(profile.get("interests", []))
    current_interests = _extract_interest_names(interests)

    # 🌟 Step 3: Merge and De-duplicate
    # This 'combined_interests' list is the secret sauce for personalization.
    combined_interests = list(set(current_interests + permanent_interests))
    interest_str = ", ".join(combined_interests) if combined_interests else "none"
    print(f"--- [DEBUG] FINAL INTERESTS SENT TO AI: {interest_str} ---")

    # Step 4: Run the Chain
    result = await suggestion_chain.ainvoke(
        {
            "mode": mode,
            "destination": destination,
            "date_reference": date_reference,
            "interests": interest_str,
            "walking_preference": walking_preference,
            "condition": condition,
            "current_summary": current_summary,
        }
    )

    # Convert Pydantic models back to dictionaries for the LangGraph state
    return {
        "activities": [act.dict() for act in result.activities],
        "suggested_summary": result.suggested_summary,
    }
