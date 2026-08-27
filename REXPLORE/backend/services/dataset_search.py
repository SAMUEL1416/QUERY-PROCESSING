"""
Orchestrates real dataset search across Hugging Face, Zenodo, DataCite, UCI,
and (optionally) Kaggle, implementing the required fallback priority:

    1. EXACT ORIGINAL DATASET  (name closely matches the paper's mention)
    2. REAL ALTERNATIVE DATASET (real repository result, not a confirmed match)
    3. Neither found -> caller may offer a SYNTHETIC dataset as a last resort

Never invents a dataset, DOI, or URL: every result returned here traces back
to a live response from one of the source services.
"""
import concurrent.futures
import difflib
import logging
from dataclasses import dataclass
from typing import List, Optional

from services import huggingface_service, zenodo_service, datacite_service, uci_service, kaggle_service

logger = logging.getLogger(__name__)

EXACT_MATCH_THRESHOLD = 0.82

SOURCES = [
    ("Hugging Face Datasets", huggingface_service.search),
    ("Zenodo", zenodo_service.search),
    ("DataCite", datacite_service.search),
    ("UCI Machine Learning Repository", uci_service.search),
    ("Kaggle", kaggle_service.search),
]


@dataclass
class DatasetSearchResult:
    kind: str          # "original" | "alternative" | "not_found"
    status: str         # "available" | "unavailable"
    name: Optional[str] = None
    repository: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    relevance_reason: Optional[str] = None
    all_candidates: Optional[List[dict]] = None


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _collect_candidates(mentioned_name: str, limit_per_source: int = 5) -> List[dict]:
    """
    Queries every dataset repository for this mention. Each provider is an
    independent, synchronous HTTP call (see e.g. huggingface_service.search),
    so running them concurrently on a small thread pool cuts wall-clock time
    from "sum of every provider's latency" to "the slowest single provider",
    with no change to which providers are queried, their parameters, or how
    results are combined.

    A failing provider is isolated exactly as before (logged, contributes no
    candidates) and never blocks or cancels the others. Results are re-assembled
    in the original SOURCES order so downstream tie-breaking (max() picks the
    first-encountered best match) is unaffected by which provider happens to
    respond first.
    """
    results_by_source: List[Optional[list]] = [None] * len(SOURCES)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        future_to_index = {
            executor.submit(search_fn, mentioned_name, limit_per_source): idx
            for idx, (_source_name, search_fn) in enumerate(SOURCES)
        }
        for future in concurrent.futures.as_completed(future_to_index):
            idx = future_to_index[future]
            source_name = SOURCES[idx][0]
            try:
                results_by_source[idx] = future.result()
            except Exception as exc:  # noqa: BLE001 - never let one source crash the whole search
                logger.warning("%s search raised an exception: %s", source_name, exc)
                results_by_source[idx] = []

    candidates: List[dict] = []
    for results in results_by_source:
        candidates.extend(results or [])
    return candidates


def search_dataset(mentioned_name: str) -> DatasetSearchResult:
    candidates = _collect_candidates(mentioned_name)

    if not candidates:
        return DatasetSearchResult(kind="not_found", status="unavailable", all_candidates=[])

    # Look for an exact/near-exact match first.
    best = max(candidates, key=lambda c: _similarity(mentioned_name, c.get("name") or ""))
    best_score = _similarity(mentioned_name, best.get("name") or "")

    if best_score >= EXACT_MATCH_THRESHOLD:
        return DatasetSearchResult(
            kind="original",
            status="available",
            name=best["name"],
            repository=best["repository"],
            doi=best.get("doi"),
            url=best.get("url"),
            description=best.get("description"),
            relevance_reason=None,
            all_candidates=candidates,
        )

    # No confident exact match -> best candidate becomes a labeled alternative.
    return DatasetSearchResult(
        kind="alternative",
        status="available",
        name=best["name"],
        repository=best["repository"],
        doi=best.get("doi"),
        url=best.get("url"),
        description=best.get("description"),
        relevance_reason=(
            f"Closest publicly available match found for the mentioned dataset "
            f"\"{mentioned_name}\" (name similarity {best_score:.0%}). "
            f"This is not confirmed as the exact dataset used in the paper."
        ),
        all_candidates=candidates,
    )
