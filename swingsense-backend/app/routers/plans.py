from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TrainingPlan
from pydantic import BaseModel, Field
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PlanInput(BaseModel):
    years_played: int = Field(..., ge=0, le=80)
    handicap: float = Field(..., ge=0, le=54)
    strengths: str = Field(..., min_length=3, max_length=500)
    weaknesses: str = Field(..., min_length=3, max_length=500)
    goals: str = Field(..., min_length=3, max_length=500)

PLAN_PROMPT_TEMPLATE = (
    "You are SwingSense, a golf coach. Create a personalized 4-week training plan for this player:\n"
    "- Years played: {years_played}\n"
    "- Handicap: {handicap}\n"
    "- Strengths: {strengths}\n"
    "- Weaknesses: {weaknesses}\n"
    "- Goals: {goals}\n"
    "Give weekly focus, drills, and tips. Use concise bullet points."
)

@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_plan(body: PlanInput, db: Session = Depends(get_db)):
    prompt = PLAN_PROMPT_TEMPLATE.format(
        years_played=body.years_played,
        handicap=body.handicap,
        strengths=body.strengths,
        weaknesses=body.weaknesses,
        goals=body.goals,
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are a helpful golf coach."},
                {"role": "user", "content": prompt},
            ],
        )
        plan_text = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    plan = TrainingPlan(
        plan=plan_text,
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
def get_current_plan(db: Session = Depends(get_db)):
    plan = db.query(TrainingPlan).order_by(TrainingPlan.created_at.desc()).first()
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
