"""
Keyword retrieval fallback for query processing, used when semantic
embeddings cannot be computed (model unavailable / index missing).
Uses simple TF-IDF-style scoring via scikit-learn's TfidfVectorizer,
falling back further to raw term-overlap counting if sklearn is unavailable.
"""
from typing import List, Optional


def keyword_search(query: str, chunks: List[dict], top_k: int = 5) -> List[dict]:
    """
    chunks: [{"text": str, "section_name": str, "page_number": int|None}, ...]
    Returns top_k chunks ranked by relevance, each with an added "score" key.
    """
    if not chunks:
        return []

    texts = [c["text"] for c in chunks]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        matrix = vectorizer.fit_transform(texts + [query])
        query_vec = matrix[-1]
        doc_matrix = matrix[:-1]
        sims = cosine_similarity(query_vec, doc_matrix)[0]
        ranked = sorted(range(len(texts)), key=lambda i: sims[i], reverse=True)[:top_k]
        return [
            {**chunks[i], "score": float(sims[i])}
            for i in ranked if sims[i] > 0
        ]
    except Exception:
        # Last-resort fallback: raw overlap of lowercase query tokens.
        query_terms = set(query.lower().split())
        scored = []
        for c in chunks:
            terms = set(c["text"].lower().split())
            overlap = len(query_terms & terms)
            if overlap:
                scored.append({**c, "score": float(overlap)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
