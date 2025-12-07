# app/api/ingest.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List
from ..core.logger import logger
from ..core.metrics import METRICS
from ..services.pdf_loader import extract_pages_text
from ..services.text_chunker import chunk_page_texts
from ..services.vectorstore import get_vectorstore
from ..db import SessionLocal
from ..models.document import Document
from ..models.chunks import Chunk
import uuid
import os

router = APIRouter()

@router.post("/ingest", tags=["ingest"])
async def ingest(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None, webhook_url: str = None):
    """
    Upload 1..n PDFs. Extract & index. Optional webhook_url to be notified when complete.
    """
    METRICS.inc("ingest_count", 1)
    saved_ids = []
    db = SessionLocal()
    vs = get_vectorstore()
    for f in files:
        content = await f.read()
        file_id = str(uuid.uuid4())
        filename = f.filename or f"{file_id}.pdf"
        pdf_path = os.path.join("data", "uploads", f"{file_id}_{filename}")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "wb") as fh:
            fh.write(content)
        # extract text and pages
        full_text, pages = extract_pages_text(pdf_path)
        # save full text
        text_path = os.path.join("data", "texts", f"{file_id}.txt")
        with open(text_path, "w", encoding="utf-8") as tf:
            tf.write(full_text)
        # chunk large pages
        chunks = chunk_page_texts(pages)
        # persist metadata to DB
        doc = Document(
            id=file_id,
            filename=filename,
            num_pages=len(pages),
            path_pdf=pdf_path,
            path_text=text_path
        )
        db.add(doc)
        db.commit()
        # persist chunks
        chunk_docs_for_index = []
        for c in chunks:
            cid = str(uuid.uuid4())
            ch = Chunk(
                id=cid,
                document_id=file_id,
                page_no=c["page_no"],
                char_start=c["char_start"],
                char_end=c["char_end"],
                text=c["text"]
            )
            db.add(ch)
            # prepare for vectorstore
            chunk_docs_for_index.append({
                "document_id": file_id,
                "page_no": c["page_no"],
                "char_start": c["char_start"],
                "char_end": c["char_end"],
                "text": c["text"]
            })
        db.commit()
        # index embeddings (could be backgrounded)
        def _index():
            try:
                vs.add(chunk_docs_for_index)
            except Exception as e:
                logger.exception("Vector store add failed: %s", e)
        if background_tasks:
            background_tasks.add_task(_index)
        else:
            _index()
        saved_ids.append(file_id)
    # optional webhook notify
    if webhook_url:
        import asyncio, aiohttp
        async def _emit():
            try:
                async with aiohttp.ClientSession() as s:
                    await s.post(webhook_url, json={"event":"ingest_complete","document_ids":saved_ids})
            except Exception as e:
                logger.exception("webhook emit failed: %s", e)
        if background_tasks:
            background_tasks.add_task(_emit)
        else:
            import asyncio
            asyncio.create_task(_emit())
    return {"document_ids": saved_ids}
