# app/services/extractors.py
import re
from ..services.llm_client import call_openai_completion
from ..core.config import OPENAI_KEY
from ..core.logger import logger

def heuristic_extract_fields(text: str):
    """
    Basic regex heuristics for common contract fields. Returns dict.
    """
    out = {}
    # parties: look for 'between X and Y' or 'this agreement is between'
    parties = re.findall(r"between\s+([A-Z][A-Za-z0-9&\s,\.]+?)\s+and\s+([A-Z][A-Za-z0-9&\s,\.]+?)[\.,\n]", text, flags=re.I)
    if parties:
        unique = []
        for a, b in parties:
            if a.strip() not in unique:
                unique.append(a.strip())
            if b.strip() not in unique:
                unique.append(b.strip())
        out["parties"] = unique[:10]
    else:
        # fallback simple company name pattern
        orgs = re.findall(r"(?:Company|Provider|Supplier|Client|Customer)[:\s]*([A-Z][A-Za-z0-9 &,\.]+)", text)
        out["parties"] = list(dict.fromkeys(orgs))[:10] if orgs else []

    # effective date
    m = re.search(r"(effective\s+date[:\s]*)([A-Za-z0-9,\s]+)", text, flags=re.I)
    out["effective_date"] = m.group(2).strip() if m else None

    # governing law
    m = re.search(r"(governing law[:\s]*)([A-Za-z\s,]+)", text, flags=re.I)
    out["governing_law"] = m.group(2).strip() if m else None

    # term
    m = re.search(r"(term[:\s]*)([A-Za-z0-9\s,]+)", text, flags=re.I)
    out["term"] = m.group(2).strip() if m else None

    # liability cap
    m = re.search(r"(liabilit(?:y|ies) cap[:\s]*)([\$\d,\.]+\s*[A-Za-z]{0,3})", text, flags=re.I)
    out["liability_cap"] = m.group(2).strip() if m else None

    return out

def llm_extract_fields(text: str):
    if not OPENAI_KEY:
        logger.info("OpenAI not configured; falling back to heuristic extract.")
        return heuristic_extract_fields(text)
    prompt = (
        "Extract the following fields from the contract text and return valid JSON only.\n\n"
        "Fields: parties (array of party names), effective_date, term, governing_law, payment_terms, "
        "termination, auto_renewal, confidentiality, indemnity, liability_cap (as {amount,currency}), signatories (list of {name,title}).\n\n"
        "Contract text:\n"
        f"{text}\n\n"
        "Return only JSON."
    )
    try:
        res = call_openai_completion(prompt, max_tokens=512, temperature=0.0)
        import json
        parsed = json.loads(res)
        return parsed
    except Exception as e:
        logger.exception("LLM extract failed, falling back: %s", e)
        return heuristic_extract_fields(text)
