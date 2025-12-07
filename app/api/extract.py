# app/api/extract.py
from fastapi import APIRouter, HTTPException
from ..db import SessionLocal
from ..models.document import Document
from ..services.extractors import llm_extract_fields, heuristic_extract_fields
from ..core.metrics import METRICS

router = APIRouter()

@router.post("/extract", tags=["extract"])
def extract(payload: dict):
    """
    Given {"document_id":"..."} returns structured fields.
    """
    METRICS.inc("extract_count", 1)
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(400, detail="document_id required")
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, detail="document not found")
    # read text
    with open(doc.path_text, "r", encoding="utf-8") as f:
        txt = f.read()
    # use LLM extractor if configured; otherwise heuristic
    out = llm_extract_fields(txt)
    # ensure some shape
    if not isinstance(out, dict):
        out = heuristic_extract_fields(txt)
    return {"document_id": doc_id, **out}
