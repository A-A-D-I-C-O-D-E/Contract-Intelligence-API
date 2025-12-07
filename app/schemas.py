# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IngestResponse(BaseModel):
    document_ids: List[str]

class ExtractResponse(BaseModel):
    document_id: str
    parties: List[str] = []
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[str] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[Dict[str, Any]] = None
    signatories: List[Dict[str, str]] = []

class AskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    top_k: int = 4
    webhook_url: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]] = []

class AuditFinding(BaseModel):
    document_id: str
    severity: str
    title: str
    evidence: List[Dict[str, Any]]
    explanation: str
