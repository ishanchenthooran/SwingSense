from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json

from app.core.config import settings
from app.rag.retrieve import retrieve
from app.rag.schemas import RetrievedChunk

router = APIRouter()

NUM_RESOURCES = 3
CANDIDATE_K = 10  # over-fetch so we can keep one chunk per source page
FALLBACK_CHARS = 240
# Same floor scripts/validate_retrieval.py's quality gate uses for a "good"
# top-1 match. Below this, corpus coverage for the issue is too thin to
# present the match as a confident answer (CLAUDE.md §1/§7: don't present
# weak matches as if they were solid).
MIN_CONFIDENCE_SCORE = 0.5


def _pick_resources(results: List[RetrievedChunk]) -> List[RetrievedChunk]:
    """Top-scoring chunks above the confidence floor, at most one per (source, page)."""
    picked: List[RetrievedChunk] = []
    seen = set()
    for r in results:
        if r.score < MIN_CONFIDENCE_SCORE:
            continue
        key = (r.chunk.source, r.chunk.page)
        if key in seen:
            continue
        seen.add(key)
        picked.append(r)
        if len(picked) == NUM_RESOURCES:
            break
    return picked


def _fallback_text(chunk_text: str) -> str:
    """Extractive description used when the LLM step fails: a slice of the chunk itself."""
    return " ".join(chunk_text.split())[:FALLBACK_CHARS].strip()


def _summarize_chunks(issue: str, picked: List[RetrievedChunk]) -> List[Dict[str, str]]:
    """
    Ask the LLM to phrase a title/description for each retrieved chunk.
    It may only restate what is in the chunk; the set of resources is fixed by retrieval.
    Falls back to extractive text per item if the call or parsing fails.
    """
    fallback = [
        {"title": r.chunk.title or "Untitled", "description": _fallback_text(r.chunk.text)}
        for r in picked
    ]

    excerpts = "\n\n".join(
        f"[{i}]\n{r.chunk.text[:1500]}" for i, r in enumerate(picked)
    )
    prompt = (
        f'A golfer is looking for help with: "{issue}".\n'
        "Below are numbered excerpts from a golf reference corpus. For EACH excerpt write:\n"
        '- "title": a short friendly title (max 8 words) describing what the excerpt covers\n'
        '- "description": 1-2 sentences summarizing ONLY what the excerpt says\n'
        "Every statement must be directly stated in the excerpt. Do NOT use outside golf "
        "knowledge: no causes, fixes, drills, rule numbers, or links unless the excerpt says them. "
        "Excerpts are often garbled multi-column text; if only a fragment is clear, describe just "
        "that fragment. If an excerpt is unreadable or unrelated, "
        'say so plainly (e.g. "Glossary excerpt; only briefly mentions the issue").\n\n'
        f"{excerpts}\n\n"
        'Return ONLY a JSON array with one object per excerpt, in order: '
        '[{"title": "...", "description": "..."}]'
    )

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "You summarize provided text faithfully and respond only in raw JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        parsed = json.loads(content)
        if not isinstance(parsed, list) or len(parsed) != len(picked):
            return fallback
        out = []
        for item, fb in zip(parsed, fallback):
            title = str(item.get("title", "")).strip() if isinstance(item, dict) else ""
            desc = str(item.get("description", "")).strip() if isinstance(item, dict) else ""
            out.append({"title": title or fb["title"], "description": desc or fb["description"]})
        return out
    except Exception:
        return fallback


@router.get("/")
async def get_resources(
    issue: Optional[str] = Query(None, description="Filter resources by issue tag"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get resources related to a specific swing issue.
    Resources are the top matches retrieved from the local corpus (RAG index);
    each carries its source document and page as the citation. No external URLs.
    """
    if not issue or not issue.strip():
        raise HTTPException(status_code=400, detail="Please provide an issue to search for.")

    try:
        results = retrieve(issue, k=CANDIDATE_K)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=503, detail=f"Retrieval unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Retrieval error: {e}")

    picked = _pick_resources(results)
    summaries = _summarize_chunks(issue, picked) if picked else []

    resources: List[Dict[str, Any]] = []
    for i, (r, s) in enumerate(zip(picked, summaries), start=1):
        resources.append({
            "id": i,
            "title": s["title"],
            "description": s["description"],
            "url": None,  # corpus is local; there is no external link to offer
            "source": r.chunk.source,
            "page": r.chunk.page,
            "citation": f"{r.chunk.source}, p. {r.chunk.page}" if r.chunk.page is not None else r.chunk.source,
            "chunk_id": r.chunk.id,
            "score": round(r.score, 4),
        })

    response: Dict[str, Any] = {"resources": resources, "filter": issue, "user_id": current_user["user_id"]}
    if len(resources) < NUM_RESOURCES:
        response["note"] = (
            "Corpus coverage for this issue is limited, so fewer high-confidence "
            "resources were found than usual."
            if resources
            else "The corpus doesn't have strong coverage for this issue yet."
        )
    return response
