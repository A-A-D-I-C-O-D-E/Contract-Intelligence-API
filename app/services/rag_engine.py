# app/services/rag_engine.py

import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from ..core.config import EMBED_MODEL
from ..core.logger import logger
from .llm_client import call_openai_completion, is_enabled
from .vectorstore import get_vectorstore
import json

class RagEngine:
    """
    Full LLM-driven RAG pipeline:
        embed question → retrieve top-k chunks → build prompt → LLM → structured JSON answer + citations.
    """

    def __init__(self):
        logger.info("Initializing RAG Engine...")
        self.model = SentenceTransformer(EMBED_MODEL)
        self.store = get_vectorstore()
        logger.info(f"RAG Engine ready. Model={EMBED_MODEL}")

    # ----------------------------------------
    # Embed user query
    # ----------------------------------------
    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode([query], show_progress_bar=False)[0]

    # ----------------------------------------
    # Retrieve top-k chunks
    # ----------------------------------------
    def retrieve(self, query: str, document_ids: Optional[List[str]], top_k: int = 6) -> List[Dict[str, Any]]:
        q_vec = self.embed_query(query)
        return self.store.search(q_vec, top_k=top_k, document_ids=document_ids)

    # ----------------------------------------
    # Build prompt for LLM
    # ----------------------------------------
    def build_prompt(self, question: str, docs: List[Dict]) -> str:
        context = ""
        for d in docs:
            context += f"[Document: {d['document_id']} | Page: {d['page_no']}]\n{d['text']}\n---\n"

        prompt = f"""
You are a legal contract analyst. Answer strictly using ONLY the context below.
Quote relevant document IDs and pages. Do not invent information.
If the answer is missing, respond: "The document does not contain this information."

QUESTION:
{question}

CONTEXT:
{context}

Return valid JSON exactly like this:
{{
  "answer": "<concise text answer>",
  "citations": [
     {{"document_id": "...", "page_no": ..., "snippet": "..."}}
  ]
}}
"""
        return prompt

    # ----------------------------------------
    # Main RAG answer using OpenAI
    # ----------------------------------------
    def answer(self, question: str, document_ids: Optional[List[str]] = None, top_k: int = 6) -> Dict[str, Any]:
        """
        Get an answer to the question using retrieved document chunks and LLM.
        Returns a dict with "answer" and "citations".
        """
        # Retrieve chunks
        retrieved = self.retrieve(question, document_ids, top_k)

        if not retrieved:
            return {"answer": "No relevant content found", "citations": []}

        # If OpenAI is not enabled, return raw concatenated retrieved text as fallback
        if not is_enabled():
            logger.warning("OpenAI disabled — returning raw retrieved content as fallback.")
            return {
                "answer": " ".join([r["text"][:500] for r in retrieved]),
                "citations": [
                    {"document_id": r["document_id"], "page_no": r["page_no"], "snippet": r["text"][:250]}
                    for r in retrieved
                ]
            }

        # Build prompt
        prompt = self.build_prompt(question, retrieved)

        try:
            llm_output = call_openai_completion(prompt, max_tokens=500, temperature=0.0)
            result = json.loads(llm_output)
            # Ensure citations have proper structure
            if "citations" not in result or not isinstance(result["citations"], list):
                result["citations"] = [
                    {"document_id": r["document_id"], "page_no": r["page_no"], "snippet": r["text"][:250]}
                    for r in retrieved
                ]
            return result
        except Exception as e:
            logger.error("LLM output invalid JSON → returning fallback with citations.", exc_info=e)
            return {
                "answer": llm_output.strip() if llm_output else "No answer generated",
                "citations": [
                    {"document_id": r["document_id"], "page_no": r["page_no"], "snippet": r["text"][:250]}
                    for r in retrieved
                ]
            }


# ------------------------------
# Singleton instance
# ------------------------------
rag_engine = RagEngine()

def get_rag_engine():
    return rag_engine
