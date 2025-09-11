from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os, json

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.get("/")
async def get_resources(
    issue: Optional[str] = Query(None, description="Filter resources by issue tag"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get resources related to a specific swing issue.
    Uses OpenAI to suggest resources with title, description, and url.
    """
    if not issue:
        raise HTTPException(status_code=400, detail="Please provide an issue to search for.")

    try:
        prompt = f"""
        You are SwingSense, a golf coach.
        Provide exactly 3 useful online resources (articles, videos, drills) 
        that help a golfer fix the issue: "{issue}".

        Return ONLY valid JSON in this format:
        [
          {{
            "id": 1,
            "title": "Fixing a Slice with Driver",
            "description": "Step-by-step drills to stop slicing your driver.",
            "url": "https://example.com/fix-slice"
          }},
          {{
            "id": 2,
            "title": "...",
            "description": "...",
            "url": "..."
          }}
        ]
        """

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,  # lower temp for structured output
            messages=[
                {"role": "system", "content": "You are a helpful golf coach that ONLY responds in raw JSON."},
                {"role": "user", "content": prompt}
            ],
        )

        content = resp.choices[0].message.content.strip()

        # Try parsing JSON strictly
        try:
            resources: List[Dict[str, Any]] = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=502, detail=f"Invalid JSON returned by AI: {content[:200]}...")

        return {"resources": resources, "filter": issue, "user_id": current_user["user_id"]}

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")