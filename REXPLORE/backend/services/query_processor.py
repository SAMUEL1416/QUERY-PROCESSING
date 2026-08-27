"""
Query processing pipeline:
  query cleaning -> normalization -> semantic retrieval (embedding_service)
  -> keyword fallback (retrieval_service) if embeddings unavailable
  -> top-k context -> paper-grounded EXTRACTIVE answer -> page/section sources.

The "answer" is assembled only from retrieved passages - never generated
freely - so it cannot hallucinate facts not present in the paper.
"""
import re
from dataclasses import dataclass
from typing import List

from services import embedding_service, retrieval_service

NOT_FOUND = "The requested information was not found in the available paper content."


@dataclass
class SourceRef:
    section_name: str
    page_number: int | None
    snippet: str
    score: float


@dataclass
class QueryResult:
    answer: str
    sources: List[SourceRef]
    retrieval_method: str  # "semantic" | "keyword_fallback"


def clean_query(raw: str) -> str:
    q = raw.strip()
    q = re.sub(r"\s+", " ", q)
    return q


def _load_chunks_for_keyword_fallback(paper_id: int, db_sections) -> List[dict]:
    """Builds keyword-search-ready chunks directly from DB sections when no semantic index exists."""
    chunks = []
    for sec in db_sections:
        text = sec.raw_text or ""
        # simple paragraph-level split for keyword search granularity
        for para in re.split(r"\n{1,}", text):
            para = para.strip()
            if len(para) > 40:
                chunks.append({"text": para, "section_name": sec.name, "page_number": sec.page_number})
        if not text:
            continue
    return chunks


def _synthesize_answer(question: str, retrieved: List[dict]) -> str:
    if not retrieved:
        return NOT_FOUND
    # Extractive synthesis: stitch the top passages together, most relevant first,
    # trimmed to keep the answer readable.
    parts = []
    for r in retrieved[:3]:
        snippet = r["text"].strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rsplit(" ", 1)[0] + "..."
        parts.append(snippet)
    return "\n\n".join(parts)


def process_query(paper_id: int, question: str, db_sections) -> QueryResult:
    cleaned = clean_query(question)

    retrieved = []
    method = "semantic"
    try:
        retrieved = embedding_service.semantic_search(paper_id, cleaned, top_k=5)
    except embedding_service.EmbeddingUnavailable:
        method = "keyword_fallback"
        chunks = _load_chunks_for_keyword_fallback(paper_id, db_sections)
        retrieved = retrieval_service.keyword_search(cleaned, chunks, top_k=5)

    if not retrieved:
        return QueryResult(answer=NOT_FOUND, sources=[], retrieval_method=method)

    answer = _synthesize_answer(cleaned, retrieved)
    sources = [
        SourceRef(
            section_name=r["section_name"],
            page_number=r.get("page_number"),
            snippet=(r["text"][:220] + "...") if len(r["text"]) > 220 else r["text"],
            score=round(float(r.get("score", 0.0)), 4),
        )
        for r in retrieved
    ]
    return QueryResult(answer=answer, sources=sources, retrieval_method=method)
