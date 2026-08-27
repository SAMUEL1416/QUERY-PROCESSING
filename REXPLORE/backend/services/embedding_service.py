"""
Wraps sentence-transformers/all-MiniLM-L6-v2 for building and querying a
per-paper semantic index. The model is loaded lazily (first use) since it
requires a one-time download from Hugging Face on the host machine.

Index format on disk (backend/indexes/paper_<id>.npz + paper_<id>_chunks.json):
  - embeddings: float32 array [num_chunks, dim]
  - chunks.json: [{"text": str, "section_name": str, "page_number": int}, ...]

If the model cannot be loaded (no internet on first run, package missing,
etc.), embedding functions raise EmbeddingUnavailable so callers can fall
back to keyword retrieval, per the spec's required fallback.
"""
import json
import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

_model = None  # lazy singleton
_index_cache: dict = {}  # paper_id -> {"mtime": float, "embeddings": np.ndarray, "chunks": list}


class EmbeddingUnavailable(Exception):
    pass


@dataclass
class Chunk:
    text: str
    section_name: str
    page_number: Optional[int]


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            settings = get_settings()
            _model = SentenceTransformer(settings.embedding_model)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load embedding model: %s", exc)
            raise EmbeddingUnavailable(str(exc)) from exc
    return _model


def _chunk_text(text: str, max_words: int = 120, overlap: int = 20) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, max_words - overlap)
    for start in range(0, len(words), step):
        chunk_words = words[start:start + max_words]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
        if start + max_words >= len(words):
            break
    return chunks


def build_chunks_from_sections(sections) -> List[Chunk]:
    """sections: iterable of objects with .name, .page_number, .raw_text"""
    chunks: List[Chunk] = []
    for sec in sections:
        for piece in _chunk_text(sec.raw_text or ""):
            chunks.append(Chunk(text=piece, section_name=sec.name, page_number=sec.page_number))
    return chunks


def _index_paths(paper_id: int):
    settings = get_settings()
    emb_path = os.path.join(settings.index_dir, f"paper_{paper_id}.npy")
    chunks_path = os.path.join(settings.index_dir, f"paper_{paper_id}_chunks.json")
    return emb_path, chunks_path


def build_and_save_index(paper_id: int, chunks: List[Chunk]) -> int:
    """Embeds all chunks and persists them. Returns number of chunks indexed."""
    if not chunks:
        return 0
    model = _get_model()
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    emb_path, chunks_path = _index_paths(paper_id)
    np.save(emb_path, embeddings)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"text": c.text, "section_name": c.section_name, "page_number": c.page_number} for c in chunks],
            f,
        )
    return len(chunks)


def index_exists(paper_id: int) -> bool:
    emb_path, chunks_path = _index_paths(paper_id)
    return os.path.exists(emb_path) and os.path.exists(chunks_path)


def warm_up():
    """
    Loads the embedding model into memory now, if it isn't already.
    Call this once at process startup (see app/main.py) so the slow,
    one-time sentence-transformers import + weight load happens during
    boot instead of blocking the first paper's "Building Semantic Index"
    stage.
    """
    _get_model()


def _load_index(paper_id: int):
    """
    Loads a paper's embeddings + chunk metadata from disk, reusing an
    in-memory copy when the index file hasn't changed since it was last
    loaded. Every query against the same paper previously re-read and
    re-parsed the same .npy/.json files from disk; the index is immutable
    once built, so this is safe to cache.

    Cache key includes the file's mtime, so a rebuilt index (e.g. after
    reprocessing a paper) is picked up automatically on the next call
    instead of serving stale data - no manual invalidation needed.
    """
    emb_path, chunks_path = _index_paths(paper_id)
    if not (os.path.exists(emb_path) and os.path.exists(chunks_path)):
        raise EmbeddingUnavailable("No semantic index found for this paper.")

    mtime = os.path.getmtime(emb_path)
    cached = _index_cache.get(paper_id)
    if cached is not None and cached["mtime"] == mtime:
        return cached["embeddings"], cached["chunks"]

    embeddings = np.load(emb_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunk_meta = json.load(f)

    _index_cache[paper_id] = {"mtime": mtime, "embeddings": embeddings, "chunks": chunk_meta}
    return embeddings, chunk_meta


def semantic_search(paper_id: int, query: str, top_k: int = 5):
    """
    Returns a list of dicts: {text, section_name, page_number, score}
    ranked by cosine similarity. Raises EmbeddingUnavailable if the model
    or index cannot be used, so the caller can fall back to keyword search.
    """
    embeddings, chunk_meta = _load_index(paper_id)
    model = _get_model()

    query_vec = model.encode([query], normalize_embeddings=True)[0]
    # embeddings are already normalized -> cosine similarity == dot product
    scores = embeddings @ query_vec
    top_idx = np.argsort(-scores)[:top_k]

    results = []
    for idx in top_idx:
        meta = chunk_meta[int(idx)]
        results.append({
            "text": meta["text"],
            "section_name": meta["section_name"],
            "page_number": meta["page_number"],
            "score": float(scores[idx]),
        })
    return results
