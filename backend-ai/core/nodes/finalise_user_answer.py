from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from core.state import TripWeaveState


class FinalAnswerResult(BaseModel):
    final_answer: str = Field(description="A clear, friendly user-facing response.")


llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0.2,
)

structured_llm = llm.with_structured_output(FinalAnswerResult)

final_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are TripWeave's user-facing travel assistant.

Turn the workflow result into a natural, concise, helpful response.

Rules:
- Sound clear and polished.
- Be specific when possible.
- Keep it short, usually 2 to 4 sentences.
- Mention important persisted changes if relevant.
- If suggestions exist, include them naturally as options.
- Do not mention internal payloads, IDs, graph nodes, or database details.
""",
        ),
        (
            "human",
            """Intent: {intent}
Summary: {final_summary}
Suggestions: {alternative_suggestions}
Destination: {destination}
Date reference: {date_reference}
Walking preference: {walking_preference}
""",
        ),
    ]
)

final_answer_chain = final_answer_prompt | structured_llm


async def finalise_user_answer(state: TripWeaveState) -> dict:
    entities = state.get("extracted_entities", {}) or {}

    result = await final_answer_chain.ainvoke(
        {
            "intent": getattr(state.get("intent"), "value", state.get("intent", "unknown")),
            "final_summary": state.get("final_summary", "Your trip update is ready."),
            "alternative_suggestions": ", ".join(state.get("alternative_suggestions", []) or []),
            "destination": entities.get("destination") or "your trip",
            "date_reference": entities.get("date_reference") or "today",
            "walking_preference": entities.get("walking_preference") or "unspecified",
        }
    )

    return {
        "final_answer": result.final_answer
    }
