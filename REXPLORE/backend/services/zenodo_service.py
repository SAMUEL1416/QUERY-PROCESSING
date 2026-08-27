"""
Searches the real Zenodo public API for datasets.
Docs: https://developers.zenodo.org/#list36
No authentication required for public search.
"""
import logging
from typing import List

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://zenodo.org/api/records"


def search(query: str, limit: int = 5) -> List[dict]:
    settings = get_settings()
    try:
        resp = requests.get(
            BASE_URL,
            params={"q": query, "type": "dataset", "size": limit, "sort": "bestmatch"},
            timeout=settings.external_api_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Zenodo dataset search failed for %r: %s", query, exc)
        return []
    except ValueError as exc:
        logger.warning("Zenodo dataset search returned invalid JSON for %r: %s", query, exc)
        return []

    results = []
    for hit in (data.get("hits", {}) or {}).get("hits", []):
        metadata = hit.get("metadata", {}) or {}
        doi = hit.get("doi") or metadata.get("doi")
        results.append({
            "name": metadata.get("title") or "Untitled dataset",
            "repository": "Zenodo",
            "doi": doi,
            "url": hit.get("links", {}).get("self_html") or hit.get("links", {}).get("html"),
            "description": (metadata.get("description") or "No description provided by the repository.")[:600],
        })
    return results
