# app/services/vectorstore.py
import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from ..core import config
from ..core.logger import logger

class FaissVectorStore:
    def __init__(self, index_path: str = None, model_name: str = None):
        self.index_path = index_path or config.FAISS_INDEX_PATH
        self.meta_path = self.index_path + ".meta.json"
        self.model_name = model_name or config.EMBED_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                self.meta = json.load(open(self.meta_path, "r", encoding="utf-8"))
                logger.info("Loaded FAISS index with %d vectors", len(self.meta))
            except Exception as e:
                logger.warning("Failed to load faiss index, init new: %s", e)
                self.index = faiss.IndexFlatL2(self.dim)
                self.meta = []
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.meta = []

    def save(self):
        faiss.write_index(self.index, self.index_path)
        json.dump(self.meta, open(self.meta_path, "w", encoding="utf-8"))

    def add(self, docs: List[Dict[str, Any]]):
        """
        docs: list of {document_id, page_no, char_start, char_end, text}
        """
        texts = [d.get("text", "") for d in docs]
        if len(texts) == 0:
            return
        emb = self.model.encode(texts, convert_to_numpy=True).astype("float32")
        self.index.add(emb)
        for d in docs:
            self.meta.append({
                "document_id": d["document_id"],
                "page_no": d["page_no"],
                "char_start": d["char_start"],
                "char_end": d["char_end"]
            })
        self.save()

    def query(self, q: str, top_k: int = 4, filter_docs: Optional[List[str]] = None):
        q_emb = self.model.encode([q], convert_to_numpy=True).astype("float32")
        D, I = self.index.search(q_emb, top_k*3)  # fetch more and filter
        hits = []
        for idx in I[0]:
            if idx < 0 or idx >= len(self.meta):
                continue
            meta = self.meta[idx]
            if filter_docs and meta["document_id"] not in filter_docs:
                continue
            # create minimal hit; caller should fetch chunk text from DB
            hits.append({"meta_idx": idx, **meta})
            if len(hits) >= top_k:
                break
        return hits

# singleton
_store = None
def get_vectorstore():
    global _store
    if _store is None:
        _store = FaissVectorStore()
    return _store
