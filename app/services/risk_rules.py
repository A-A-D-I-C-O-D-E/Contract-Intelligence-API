# app/services/risk_rules.py
import re
from typing import List, Dict, Any

RULES = [
    {
        "id": "auto_renewal_short_notice",
        "regex": r"(auto-?renew(?:al)?|renew automatically|renewal will occur).*?(\d{1,2})\s*(day|days)",
        "description": "Auto-renewal clause with specified notice period",
        "severity": "medium",
        "post": lambda m: int(m.group(2)) if m else None
    },
    {
        "id": "unlimited_liability",
        "regex": r"(unlimited liability|no limit on liability|without limitation of liability|no cap on liability)",
        "description": "Unlimited liability or no-cap language",
        "severity": "high",
    },
    {
        "id": "broad_indemnity",
        "regex": r"(indemnif(?:y|ies|ication)|hold harmless).*?(indemnify|hold harmless|defend)",
        "description": "Potentially broad indemnity",
        "severity": "medium",
    },
    {
        "id": "missing_confidentiality",
        "regex": r"(confidentiality|confidential information|non-?disclos)",
        "description": "Confidentiality clause existence check",
        "severity": "low",
    }
]

def audit_text_for_risks(text: str, document_id: str, page_no: int):
    findings = []
    lower = text.lower()
    for rule in RULES:
        try:
            m = re.search(rule["regex"], lower, flags=re.I | re.S)
        except re.error:
            m = None
        if m:
            ev = {
                "document_id": document_id,
                "page_no": page_no,
                "match_text": m.group(0)[:1000]
            }
            extra = {}
            if "post" in rule:
                try:
                    extra_val = rule["post"](m)
                    extra["value"] = extra_val
                except Exception:
                    extra["value"] = None
            findings.append({
                "id": rule["id"],
                "title": rule["description"],
                "severity": rule["severity"],
                "evidence": ev,
                "extra": extra
            })
    return findings
