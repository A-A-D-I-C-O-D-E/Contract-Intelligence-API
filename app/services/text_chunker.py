# app/services/text_chunker.py
from typing import List, Dict

def chunk_page_texts(pages: List[dict], max_chars: int = 1000, overlap: int = 200):
    """
    Given page-based entries, further split very large pages into smaller chunks.
    Returns list of chunks with page_no and char offsets relative to page text start.
    """
    out = []
    for p in pages:
        text = p.get("text", "")
        if not text:
            out.append({
                "page_no": p["page_no"],
                "char_start": p["char_start"],
                "char_end": p["char_end"],
                "text": ""
            })
            continue
        if len(text) <= max_chars:
            out.append({
                "page_no": p["page_no"],
                "char_start": p["char_start"],
                "char_end": p["char_end"],
                "text": text
            })
            continue
        # split into sliding windows
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunk_text = text[start:end]
            out.append({
                "page_no": p["page_no"],
                "char_start": p["char_start"] + start,
                "char_end": p["char_start"] + end,
                "text": chunk_text
            })
            if end == len(text):
                break
            start = end - overlap
    return out
