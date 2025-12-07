# app/api/stream.py
from fastapi import APIRouter, WebSocket
from ..services.vectorstore import get_vectorstore
from ..db import SessionLocal
from ..models.chunks import Chunk
from ..core.logger import logger
from ..core.metrics import METRICS
import json, asyncio

router = APIRouter()

@router.websocket("/ask/stream")
async def ask_stream(ws: WebSocket):
    """
    Expects client to send JSON: {"question":"...", "document_ids": [...], "top_k": 4}
    Server streams partial JSON messages:
      {"type":"partial", "text":"..."}
      {"type":"done", "text":"...", "citations":[...]}
    """
    await ws.accept()
    METRICS.inc("ask_count", 1)
    try:
        data = await ws.receive_text()
        req = json.loads(data)
        question = req.get("question")
        doc_ids = req.get("document_ids")
        top_k = req.get("top_k", 4)
        vs = get_vectorstore()
        hits_meta = vs.query(question, top_k=top_k, filter_docs=doc_ids)
        db = SessionLocal()
        hits = []
        for h in hits_meta:
            ch = db.query(Chunk).filter(Chunk.document_id == h["document_id"], Chunk.page_no == h["page_no"]).first()
            if ch:
                hits.append({"document_id": ch.document_id, "page_no": ch.page_no, "text": ch.text})
        # simple simulated streaming: send each chunk's first 400 chars
        for h in hits:
            snippet = h["text"][:400] if h["text"] else ""
            await ws.send_text(json.dumps({"type":"partial","text":snippet,"meta":{"document_id":h["document_id"],"page_no":h["page_no"]}}))
            await asyncio.sleep(0.15)
        # final combined answer (fallback)
        final_text = " ".join([h["text"][:800] for h in hits])[:4000]
        citations = [{"document_id":h["document_id"], "page_no":h["page_no"]} for h in hits]
        await ws.send_text(json.dumps({"type":"done","text":final_text,"citations":citations}))
    except Exception as e:
        logger.exception("stream error: %s", e)
        await ws.send_text(json.dumps({"type":"error","error":str(e)}))
    finally:
        await ws.close()
