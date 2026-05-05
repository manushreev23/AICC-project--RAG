"""
rag_retriever.py
----------------
Chunk → embed → FAISS index → retrieve.

Public API
==========
    RAGRetriever(model_name="all-MiniLM-L6-v2")
        .build(pages, outline)        # pages from pdf_extractor.extract_pdf
        .retrieve(query, top_k=15)    # returns list of relevant chunks
        .retrieve_by_section(query)   # returns {subsection_title: [chunks...]}

Each chunk is a dict:
    {"text": str, "page": int, "section": str, "score": float}
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer


# -------------------------- Chunking utilities ------------------------------ #

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _split_sentences(text: str) -> List[str]:
    sents = _SENT_SPLIT.split(text.replace("\n", " "))
    return [s.strip() for s in sents if len(s.strip()) > 10]


def _chunk_text(text: str, max_words: int = 140, overlap: int = 30) -> List[str]:
    """Greedy sentence-aware chunker with small overlap for context preservation."""
    sentences = _split_sentences(text)
    chunks, current, word_count = [], [], 0
    for s in sentences:
        w = len(s.split())
        if word_count + w > max_words and current:
            chunks.append(" ".join(current))
            # overlap: keep last few sentences
            keep, kept_words = [], 0
            for prev in reversed(current):
                kept_words += len(prev.split())
                keep.insert(0, prev)
                if kept_words >= overlap:
                    break
            current = keep[:]
            word_count = sum(len(x.split()) for x in current)
        current.append(s)
        word_count += w
    if current:
        chunks.append(" ".join(current))
    return chunks


def _nearest_section(page: int, outline: List[Dict]) -> str:
    """Pick the closest preceding heading for a given page."""
    if not outline:
        return "Content"
    best = "Content"
    for h in outline:
        if h["page"] <= page:
            best = h["title"]
        else:
            break
    return best


# ------------------------------- Retriever --------------------------------- #


class RAGRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks: List[Dict] = []

    def _ensure_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    # ---- Build ------------------------------------------------------------ #
    def build(self, pages: List[Dict], outline: List[Dict]) -> int:
        """
        Chunk every page's text, embed, store in FAISS.
        Returns number of chunks indexed.
        """
        self.chunks = []
        for p in pages:
            section = _nearest_section(p["page"], outline)
            for ch in _chunk_text(p["text"]):
                self.chunks.append(
                    {"text": ch, "page": p["page"], "section": section}
                )

        if not self.chunks:
            return 0

        model = self._ensure_model()
        texts = [c["text"] for c in self.chunks]
        emb = model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        ).astype("float32")

        self.index = faiss.IndexFlatIP(emb.shape[1])
        self.index.add(emb)
        return len(self.chunks)

    # ---- Retrieve --------------------------------------------------------- #
    def retrieve(self, query: str, top_k: int = 15, min_score: float = 0.18) -> List[Dict]:
        if not self.index or not self.chunks:
            return []
        model = self._ensure_model()
        q_emb = model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        k = min(top_k, len(self.chunks))
        scores, idxs = self.index.search(q_emb, k)
        results = []
        for s, i in zip(scores[0].tolist(), idxs[0].tolist()):
            if i < 0:
                continue
            if s < min_score:
                continue
            item = dict(self.chunks[i])
            item["score"] = float(s)
            results.append(item)
        return results

    def retrieve_by_section(
        self, query: str, top_k: int = 25, min_score: float = 0.18
    ) -> Dict[str, List[Dict]]:
        """Group retrieved chunks under their nearest heading (subsection)."""
        hits = self.retrieve(query, top_k=top_k, min_score=min_score)
        grouped: Dict[str, List[Dict]] = {}
        for h in hits:
            grouped.setdefault(h["section"], []).append(h)
        # Sort sections by best score, then by page.
        ordered = dict(
            sorted(
                grouped.items(),
                key=lambda kv: (-max(c["score"] for c in kv[1]), min(c["page"] for c in kv[1])),
            )
        )
        return ordered


