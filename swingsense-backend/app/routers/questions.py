from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import SwingQuestion, SwingFeedback

# NEW: OpenAI client
from openai import OpenAI

from app.core.config import settings
from app.rag.retrieve import retrieve
from app.rag.prompt import build_prompt

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
    feedback: str
    sources: list[str] = []
    created_at: datetime

# ---------- Helpers ----------

def _q_to_out(row: SwingQuestion) -> QuestionOut:
    return QuestionOut(id=str(row.id), question=row.question, created_at=row.created_at)

def _f_to_out(row: SwingFeedback) -> FeedbackOut:
    return FeedbackOut(id=str(row.id), feedback=row.feedback, sources=row.sources or [], created_at=row.created_at)

def generate_feedback(question_text: str) -> tuple[str, list[str]]:
    try:
        chunks = retrieve(question_text, k=5)
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
    feedback_text, sources = generate_feedback(body.question)

    # 3) save feedback linked to question
    fb = SwingFeedback(question_id=q.id, feedback=feedback_text, sources=sources)
    db.add(fb)
    db.commit()

    return {"id": str(q.id), "sources": sources}

@router.get("/feedback/", response_model=List[FeedbackOut])
def list_feedback(db: Session = Depends(get_db)):
    """Latest 50 feedback entries."""
    stmt = select(SwingFeedback).order_by(SwingFeedback.created_at.desc()).limit(50)
    rows = db.execute(stmt).scalars().all()
    return [_f_to_out(r) for r in rows]
