from __future__ import annotations

from typing import List

from app.rag.schemas import RetrievedChunk


SYSTEM_PROMPT = (
    "You are SwingSense, an expert golf coach. Answer the user's question using ONLY "
    "the context passages provided below. Each passage is labeled with its source title "
    "and drawn from a curated golf instruction corpus. If the context does not contain "
    "enough information to answer confidently, say so explicitly — do not guess or "
    "fabricate. When you use a passage, name its source inline in your answer (e.g., "
    '"According to <source title>...") using the exact title shown for that passage. '
    "Keep your response concise (under 150 words), use 3–6 numbered bullets where appropriate, "
    "and recommend at most one drill. Do not add a separate sources or references section "
    "at the end — attribution belongs inline, in the prose."
)


def build_prompt(question: str, chunks: List[RetrievedChunk]) -> tuple[List[dict], List[str]]:
    sources: List[str] = []

    if not chunks:
        context_block = "No relevant context was found in the corpus."
    else:
        passages = []
        seen: set[str] = set()
        for result in chunks:
            title = result.chunk.title or "Untitled"
            passages.append(f"Source: {title}\n{result.chunk.text}")
            if title not in seen:
                sources.append(title)
                seen.add(title)
        context_block = "\n\n".join(passages)

    user_message = f"Context:\n{context_block}\n\nQuestion: {question}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return messages, sources
