import uuid
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import RoundLog
from app.core.auth import get_current_user

router = APIRouter()

# ---------- Pydantic Schemas ----------

class RoundLogIn(BaseModel):
    round_date: date
    course_name: Optional[str] = Field(None, max_length=200)
    score: int = Field(..., ge=18, le=200)
    score_to_par: Optional[int] = Field(None, ge=-30, le=100)
    putts: Optional[int] = Field(None, ge=0, le=100)
    fairways_hit: Optional[int] = Field(None, ge=0, le=30)
    greens_in_regulation: Optional[int] = Field(None, ge=0, le=18)
    notes: Optional[str] = Field(None, max_length=2000)


class RoundLogUpdate(BaseModel):
    round_date: Optional[date] = None
    course_name: Optional[str] = Field(None, max_length=200)
    score: Optional[int] = Field(None, ge=18, le=200)
    score_to_par: Optional[int] = Field(None, ge=-30, le=100)
    putts: Optional[int] = Field(None, ge=0, le=100)
    fairways_hit: Optional[int] = Field(None, ge=0, le=30)
    greens_in_regulation: Optional[int] = Field(None, ge=0, le=18)
    notes: Optional[str] = Field(None, max_length=2000)


class RoundLogOut(BaseModel):
    id: str
    round_date: date
    course_name: Optional[str]
    score: int
    score_to_par: Optional[int]
    putts: Optional[int]
    fairways_hit: Optional[int]
    greens_in_regulation: Optional[int]
    notes: Optional[str]
    created_at: datetime


class ProgressSummary(BaseModel):
    rounds_played: int
    avg_score: Optional[float]
    best_score: Optional[int]
    avg_putts: Optional[float]
    avg_fairways_hit: Optional[float]
    avg_greens_in_regulation: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]

# ---------- Helpers ----------

def _to_out(row: RoundLog) -> RoundLogOut:
    return RoundLogOut(
        id=str(row.id),
        round_date=row.round_date,
        course_name=row.course_name,
        score=row.score,
        score_to_par=row.score_to_par,
        putts=row.putts,
        fairways_hit=row.fairways_hit,
        greens_in_regulation=row.greens_in_regulation,
        notes=row.notes,
        created_at=row.created_at,
    )


def _get_owned_round(db: Session, round_id: str, user_id: str) -> RoundLog:
    try:
        rid = uuid.UUID(round_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid round id")
    row = db.get(RoundLog, rid)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Round log not found")
    return row

# ---------- Routes ----------

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RoundLogOut)
def create_progress(
    body: RoundLogIn,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Log a new round.
    """
    row = RoundLog(user_id=current_user["user_id"], **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.get("/", response_model=List[RoundLogOut])
def get_progress(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List logged rounds, optionally filtered by date range.
    """
    stmt = select(RoundLog).where(RoundLog.user_id == current_user["user_id"])
    if start_date:
        stmt = stmt.where(RoundLog.round_date >= start_date)
    if end_date:
        stmt = stmt.where(RoundLog.round_date <= end_date)
    stmt = stmt.order_by(RoundLog.round_date.desc())
    rows = db.execute(stmt).scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/summary", response_model=ProgressSummary)
def get_progress_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggregate stats (avg score, best score, avg putts/fairways/GIR) across logged rounds.
    """
    stmt = select(
        func.count(RoundLog.id),
        func.avg(RoundLog.score),
        func.min(RoundLog.score),
        func.avg(RoundLog.putts),
        func.avg(RoundLog.fairways_hit),
        func.avg(RoundLog.greens_in_regulation),
    ).where(RoundLog.user_id == current_user["user_id"])
    if start_date:
        stmt = stmt.where(RoundLog.round_date >= start_date)
    if end_date:
        stmt = stmt.where(RoundLog.round_date <= end_date)

    rounds_played, avg_score, best_score, avg_putts, avg_fairways, avg_gir = db.execute(stmt).one()

    return ProgressSummary(
        rounds_played=rounds_played,
        avg_score=round(float(avg_score), 2) if avg_score is not None else None,
        best_score=best_score,
        avg_putts=round(float(avg_putts), 2) if avg_putts is not None else None,
        avg_fairways_hit=round(float(avg_fairways), 2) if avg_fairways is not None else None,
        avg_greens_in_regulation=round(float(avg_gir), 2) if avg_gir is not None else None,
        start_date=start_date,
        end_date=end_date,
    )


@router.put("/{round_id}", response_model=RoundLogOut)
def update_progress(
    round_id: str,
    body: RoundLogUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update fields on an existing round log owned by the current user.
    """
    row = _get_owned_round(db, round_id, current_user["user_id"])
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(
    round_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a round log owned by the current user.
    """
    row = _get_owned_round(db, round_id, current_user["user_id"])
    db.delete(row)
    db.commit()
    return None
