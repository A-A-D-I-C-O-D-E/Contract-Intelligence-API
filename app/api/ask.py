# app/api/ask.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..schemas import AskRequest
from ..db import SessionLocal
from ..models.chunks import Chunk
from ..services.vectorstore import get_vectorstore
from ..services.llm_client import call_openai_completion
from ..core.metrics import METRICS
from typing import List
from ..core.logger import logger
import json

router = APIRouter()

@router.post("/ask", tags=["ask"])
def ask(req: AskRequest, background_tasks: BackgroundTasks = None):
    """
    RAG pipeline: retrieve top-k page chunks and then call LLM (if available).
    Returns answer and citations with doc+page+char spans.
    """
    METRICS.inc("ask_count", 1)
    vs = get_vectorstore()
    db = SessionLocal()
    # find candidate hits
    hits_meta = vs.query(req.question, top_k=req.top_k, filter_docs=req.document_ids)
    hits = []
    for h in hits_meta:
        # fetch chunk text from DB by meta
        chunk = db.query(Chunk).filter(
            Chunk.document_id == h["document_id"],
            Chunk.page_no == h["page_no"]
        ).first()
        if chunk:
            hits.append({
                "document_id": chunk.document_id,
                "page_no": chunk.page_no,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "text": (chunk.text[:3000] if chunk.text else "")
            })
    citations = [{"document_id": h["document_id"], "page_no": h["page_no"], "char_start": h["char_start"], "char_end": h["char_end"]} for h in hits]
    # build prompt
    contexts = "\n\n---\n\n".join([f"Doc: {h['document_id']} Page: {h['page_no']}\n{h['text']}" for h in hits])
    if contexts.strip() == "":
        return {"answer": "No content found in documents", "citations": []}
    prompt = f"Answer the question using ONLY the provided context.\nQuestion: {req.question}\n\nContext:\n{contexts}\n\nAnswer concisely and include which document/page supports your answer."
    # call LLM if configured
    try:
        from ..core.config import OPENAI_KEY
        if OPENAI_KEY:
            answer = call_openai_completion(prompt, max_tokens=400, temperature=0.0)
        else:
            # fallback extractive: choose sentences overlapping with question tokens
            import re, heapq
            q_tokens = set(re.findall(r"\w+", req.question.lower()))
            sentences = []
            for h in hits:
                sents = re.split(r'(?<=[\.\n])\s+', h["text"])
                for s in sents:
                    score = len(q_tokens & set(re.findall(r"\w+", s.lower())))
                    if score > 0:
                        sentences.append((score, s))
            sentences.sort(reverse=True)
            top = [s for sc, s in sentences[:5]]
            answer = " ".join(top) if top else (hits[0]["text"][:500] + "...")
    except Exception as e:
        logger.exception("Error during LLM/fallback: %s", e)
        answer = "Error generating answer: " + str(e)
    # optional webhook
    if req.webhook_url:
        import aiohttp, asyncio
        async def _emit():
            try:
                async with aiohttp.ClientSession() as s:
                    await s.post(req.webhook_url, json={"event":"ask_complete","question":req.question,"answer":answer,"citations":citations})
            except Exception as ex:
                logger.exception("webhook emit failed: %s", ex)
        if background_tasks:
            background_tasks.add_task(_emit)
    return {"answer": answer, "citations": citations}
