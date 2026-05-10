"""
rag.py — Minimal local vector store using sentence-transformers embeddings.

This module provides simple functions to index text documents and retrieve
the top-k most relevant passages for a query using cosine similarity.
The store is persisted to disk at `vectorstore.pkl` so Streamlit sessions
can reuse the index.
"""
from __future__ import annotations
import os
import pickle
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_STORE_PATH = os.path.join(os.path.dirname(__file__), "vectorstore.pkl")


class VectorStore:
    def __init__(self, model_name: str = _MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        self.docs: List[str] = []
        self.embs: np.ndarray | None = None

    def index_texts(self, texts: List[str]) -> None:
        # append and recompute embeddings (small-scale; acceptable for demo)
        self.docs.extend(texts)
        new_embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        if self.embs is None:
            self.embs = new_embs
        else:
            self.embs = np.vstack([self.embs, new_embs])
        self._persist()

    def _persist(self) -> None:
        with open(_STORE_PATH, "wb") as fh:
            pickle.dump({"docs": self.docs, "embs": self.embs}, fh)

    def load(self) -> None:
        if not os.path.exists(_STORE_PATH):
            return
        with open(_STORE_PATH, "rb") as fh:
            data = pickle.load(fh)
        self.docs = data.get("docs", [])
        self.embs = data.get("embs")

    def clear(self) -> None:
        self.docs = []
        self.embs = None
        if os.path.exists(_STORE_PATH):
            os.remove(_STORE_PATH)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[int, float, str]]:
        """Return list of (index, score, doc_text) for top_k results."""
        if not self.docs or self.embs is None:
            return []
        q_emb = self.model.encode([query], convert_to_numpy=True)[0]
        # cosine similarity
        dists = (self.embs @ q_emb) / (np.linalg.norm(self.embs, axis=1) * (np.linalg.norm(q_emb) + 1e-12))
        top_idx = np.argsort(-dists)[:top_k]
        return [(int(i), float(dists[i]), self.docs[i]) for i in top_idx]


_GLOBAL_STORE: VectorStore | None = None


def get_store() -> VectorStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = VectorStore()
        _GLOBAL_STORE.load()
    return _GLOBAL_STORE


def index_texts(texts: List[str]) -> None:
    store = get_store()
    store.index_texts(texts)


def clear_store() -> None:
    store = get_store()
    store.clear()


def retrieve(query: str, top_k: int = 3) -> List[Tuple[int, float, str]]:
    store = get_store()
    return store.retrieve(query, top_k=top_k)
