from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import TrainingPlan
from app.core.config import settings
from app.core.auth import get_optional_user
from openai import OpenAI

from app.rag.retrieve import retrieve

router = APIRouter()

class PlanInput(BaseModel):
    years_played: int = Field(..., ge=0, le=80)
    handicap: float = Field(..., ge=0, le=54)
    strengths: str = Field(..., min_length=3, max_length=500)
    weaknesses: str = Field(..., min_length=3, max_length=500)
    goals: str = Field(..., min_length=3, max_length=500)

PLAN_SYSTEM_PROMPT = (
    "You are SwingSense, a golf coach. Ground the plan in the context passages provided. "
    "Each passage is labeled with its source title. Base drills and technique advice on the "
    "passages where they are relevant, and name the source inline (e.g., \"per <source title>\") "
    "using the exact title shown. Where the passages do not cover something the plan needs, "
    "you may add general coaching guidance, but say plainly that it goes beyond the provided "
    "material (e.g., \"General guidance, not from the corpus:\"). Never invent source titles "
    "or rule numbers. If no context was found, say so and label the whole plan as general guidance."
)

PLAN_PROMPT_TEMPLATE = (
    "Context:\n{context}\n\n"
    "Create a personalized 4-week training plan for this player:\n"
    "- Years played: {years_played}\n"
    "- Handicap: {handicap}\n"
    "- Strengths: {strengths}\n"
    "- Weaknesses: {weaknesses}\n"
    "- Goals: {goals}\n"
    "Give weekly focus, drills, and tips. Use concise bullet points."
)


def _build_context(chunks) -> str:
    if not chunks:
        return "No relevant context was found in the corpus."
    return "\n\n".join(
        f"Source: {r.chunk.title or 'Untitled'}\n{r.chunk.text}" for r in chunks
    )


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_plan(
    body: PlanInput,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    try:
        chunks = retrieve(f"{body.weaknesses} {body.goals}", k=5)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Retrieval error: {e}")

    prompt = PLAN_PROMPT_TEMPLATE.format(
        context=_build_context(chunks),
        years_played=body.years_played,
        handicap=body.handicap,
        strengths=body.strengths,
        weaknesses=body.weaknesses,
        goals=body.goals,
    )
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        plan_text = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    user_id = current_user["user_id"] if current_user else None
    plan = TrainingPlan(
        plan=plan_text,
        user_id=user_id,
        years_played=body.years_played,
        handicap=body.handicap,
        strengths=body.strengths,
        weaknesses=body.weaknesses,
        goals=body.goals,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"plan": plan.plan, "id": str(plan.id)}


@router.get("/current")
def get_current_plan(
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    stmt = select(TrainingPlan)
    if current_user:
        stmt = stmt.where(TrainingPlan.user_id == current_user["user_id"])
    stmt = stmt.order_by(TrainingPlan.created_at.desc()).limit(1)
    plan = db.execute(stmt).scalars().first()

    if not plan:
        return {"plan": None}
    return {
        "plan": plan.plan,
        "years_played": plan.years_played,
        "handicap": plan.handicap,
        "strengths": plan.strengths,
        "weaknesses": plan.weaknesses,
        "goals": plan.goals,
        "created_at": plan.created_at,
    }
