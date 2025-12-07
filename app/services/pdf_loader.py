# app/services/pdf_loader.py
import fitz  # PyMuPDF
from typing import Tuple, List

def extract_pages_text(pdf_path: str) -> Tuple[str, List[dict]]:
    """
    Return full_text and list of page-chunks: text per page with char ranges relative to concatenated text.
    """
    doc = fitz.open(pdf_path)
    pages = []
    all_text_parts = []
    char_cursor = 0
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        start = char_cursor
        end = start + len(text)
        pages.append({"page_no": i+1, "char_start": start, "char_end": end, "text": text})
        all_text_parts.append(text)
        char_cursor = end
    full_text = "\n".join(all_text_parts)
    return full_text, pages
