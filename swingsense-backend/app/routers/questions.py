from typing import List
from datetime import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import SwingQuestion, SwingFeedback

# NEW: OpenAI client
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- Pydantic Schemas ----------

class AskBody(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)

class QuestionOut(BaseModel):
    id: str
    question: str
    created_at: datetime

class FeedbackOut(BaseModel):
    id: str
    feedback: str
    created_at: datetime

# ---------- Helpers ----------

SYSTEM_PROMPT = (
    "You are SwingSense, a helpful golf coach. Provide concise, actionable advice "
    "tailored to the user’s specific swing issue. Use 3–6 numbered bullets, at most "
    "one drill, avoid generic boilerplate, and keep it under 120 words."
)

def _q_to_out(row: SwingQuestion) -> QuestionOut:
    return QuestionOut(id=str(row.id), question=row.question, created_at=row.created_at)

def _f_to_out(row: SwingFeedback) -> FeedbackOut:
    return FeedbackOut(id=str(row.id), feedback=row.feedback, created_at=row.created_at)

def generate_feedback(question_text: str) -> str:
    """Call OpenAI and return concise coaching feedback."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question_text},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Surface a real error so we don't quietly insert canned text
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

# ---------- Routes (match OpenAPI docs) ----------

@router.get("/questions/", response_model=List[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    """Latest 50 questions (scoped to user later if/when auth is added)."""
    stmt = select(SwingQuestion).order_by(SwingQuestion.created_at.desc()).limit(50)
    rows = db.execute(stmt).scalars().all()
    return [_q_to_out(r) for r in rows]

@router.post("/questions/", status_code=status.HTTP_201_CREATED)
def create_question(body: AskBody, db: Session = Depends(get_db)):
    """
    Insert question -> call OpenAI -> insert feedback (linked to question).
    Returns the new question id (the UI refreshes lists separately).
    """
    # 1) save the question
    q = SwingQuestion(question=body.question)
    db.add(q)
    db.flush()  # get q.id before commit

    # 2) generate real feedback
    feedback_text = generate_feedback(body.question)

    # 3) save feedback linked to question
    fb = SwingFeedback(question_id=q.id, feedback=feedback_text)
    db.add(fb)
    db.commit()

    return {"id": str(q.id)}

@router.get("/feedback/", response_model=List[FeedbackOut])
def list_feedback(db: Session = Depends(get_db)):
    """Latest 50 feedback entries."""
    stmt = select(SwingFeedback).order_by(SwingFeedback.created_at.desc()).limit(50)
    rows = db.execute(stmt).scalars().all()
    return [_f_to_out(r) for r in rows]
