# app/api/audit.py
from fastapi import APIRouter, HTTPException
from ..services.risk_rules import audit_text_for_risks
from ..db import SessionLocal
from ..models.document import Document
from ..models.chunks import Chunk
from ..core.metrics import METRICS

router = APIRouter()

@router.post("/audit", tags=["audit"])
def audit(payload: dict = None):
    """
    payload may include {"document_ids": ["id1","id2"]} or absent to check all.
    """
    METRICS.inc("audit_count", 1)
    db = SessionLocal()
    doc_ids = None
    if payload:
        doc_ids = payload.get("document_ids")
    findings = []
    if doc_ids:
        docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    else:
        docs = db.query(Document).all()
    for d in docs:
        # use chunk text per page
        chunks = db.query(Chunk).filter(Chunk.document_id == d.id).all()
        for c in chunks:
            f = audit_text_for_risks(c.text or "", d.id, c.page_no)
            for ff in f:
                findings.append(ff)
    return findings
