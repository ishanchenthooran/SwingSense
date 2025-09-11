from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile. Bootstrap user & profile rows if missing.
    """
    # TODO: Implement user and profile table creation/retrieval
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "profile": {
            "name": None,
            "age": None,
            "skill_level": None,
            "goals": []
        }
    }

@router.put("/")
async def update_me(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile fields.
    """
    # TODO: Implement profile update logic
    return {
        "message": "Profile updated successfully",
        "user_id": current_user["user_id"],
        "updated_fields": list(profile_data.keys())
    }
