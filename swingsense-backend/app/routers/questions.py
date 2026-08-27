from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import SwingQuestion, SwingFeedback
from openai import OpenAI

from app.core.config import settings
from app.core.auth import get_optional_user
from app.rag.retrieve import retrieve
from app.rag.prompt import build_prompt
from app.rag.store import DEFAULT_TOP_K

router = APIRouter()

# ---------- Pydantic Schemas ----------

class AskBody(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)

class QuestionOut(BaseModel):
    id: str
    question: str
    created_at: datetime

class FeedbackOut(BaseModel):
    id: str
    question_id: str
    feedback: str
    sources: list[str] = []
    created_at: datetime

# ---------- Helpers ----------

def _q_to_out(row: SwingQuestion) -> QuestionOut:
    return QuestionOut(id=str(row.id), question=row.question, created_at=row.created_at)

def _f_to_out(row: SwingFeedback) -> FeedbackOut:
    return FeedbackOut(
        id=str(row.id),
        question_id=str(row.question_id),
        feedback=row.feedback,
        sources=row.sources or [],
        created_at=row.created_at,
    )

def generate_feedback(question_text: str) -> tuple[str, list[str]]:
    try:
        chunks = retrieve(question_text, k=DEFAULT_TOP_K)
        messages, sources = build_prompt(question_text, chunks)
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=messages,
        )
        return resp.choices[0].message.content.strip(), sources
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

# ---------- Routes ----------

@router.get("/", response_model=List[QuestionOut])
def list_questions(
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    stmt = select(SwingQuestion)
    if current_user:
        stmt = stmt.where(SwingQuestion.user_id == current_user["user_id"])
    stmt = stmt.order_by(SwingQuestion.created_at.desc()).limit(50)
    rows = db.execute(stmt).scalars().all()
    return [_q_to_out(r) for r in rows]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_question(
    body: AskBody,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    user_id = current_user["user_id"] if current_user else None

    q = SwingQuestion(question=body.question, user_id=user_id)
    db.add(q)
    db.flush()

    feedback_text, sources = generate_feedback(body.question)

    fb = SwingFeedback(question_id=q.id, feedback=feedback_text, sources=sources)
    db.add(fb)
    db.commit()

    return {"id": str(q.id), "sources": sources}


@router.get("/feedback", response_model=List[FeedbackOut])
def list_feedback(
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    stmt = select(SwingFeedback)
    if current_user:
        stmt = stmt.join(SwingQuestion, SwingFeedback.question_id == SwingQuestion.id).where(
            SwingQuestion.user_id == current_user["user_id"]
        )
    stmt = stmt.order_by(SwingFeedback.created_at.desc()).limit(50)
    rows = db.execute(stmt).scalars().all()
    return [_f_to_out(r) for r in rows]
