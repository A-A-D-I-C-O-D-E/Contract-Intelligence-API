# app/api/webhook.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import aiohttp, asyncio
from ..core.logger import logger

router = APIRouter()

class WebhookPayload(BaseModel):
    url: HttpUrl
    event: str
    body: dict

@router.post("/webhook/events", tags=["webhook"])
async def send_webhook(payload: WebhookPayload):
    """
    Server will POST payload.body to payload.url with header X-Event:payload.event
    Useful for testing webhook emitters.
    """
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(str(payload.url), json=payload.body, headers={"X-Event": payload.event}) as resp:
                text = await resp.text()
                return {"status": resp.status, "text": text}
    except Exception as e:
        logger.exception("webhook send failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
