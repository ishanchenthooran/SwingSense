from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import UserProfile
from app.core.auth import get_current_user

router = APIRouter()


class ProfileOut(BaseModel):
    name: Optional[str] = None
    years_played: Optional[int] = None
    handicap: Optional[float] = None
    skill_level: Optional[str] = None
    goals: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    years_played: Optional[int] = Field(None, ge=0, le=80)
    handicap: Optional[float] = Field(None, ge=0, le=54)
    skill_level: Optional[str] = Field(None, max_length=50)
    goals: Optional[str] = Field(None, max_length=2000)


def _to_out(row: UserProfile) -> ProfileOut:
    return ProfileOut(
        name=row.name,
        years_played=row.years_played,
        handicap=row.handicap,
        skill_level=row.skill_level,
        goals=row.goals,
    )


def _get_or_create_profile(db: Session, user_id: str) -> UserProfile:
    profile = db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    ).scalar_one_or_none()
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/")
def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user profile. Bootstraps a profile row if this is a new user.
    """
    profile = _get_or_create_profile(db, current_user["user_id"])
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "profile": _to_out(profile),
    }


@router.put("/")
def update_me(
    body: ProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update whichever profile fields are provided.
    """
    profile = _get_or_create_profile(db, current_user["user_id"])
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return {
        "message": "Profile updated successfully",
        "user_id": current_user["user_id"],
        "profile": _to_out(profile),
    }
