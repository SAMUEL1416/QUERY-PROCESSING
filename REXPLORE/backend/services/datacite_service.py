"""
Searches the real DataCite public REST API for dataset DOIs.
Docs: https://support.datacite.org/docs/api-queries
No authentication required for public search.
"""
import logging
from typing import List

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.datacite.org/dois"


def search(query: str, limit: int = 5) -> List[dict]:
    settings = get_settings()
    try:
        resp = requests.get(
            BASE_URL,
            params={"query": query, "resource-type-id": "dataset", "page[size]": limit},
            timeout=settings.external_api_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("DataCite dataset search failed for %r: %s", query, exc)
        return []
    except ValueError as exc:
        logger.warning("DataCite dataset search returned invalid JSON for %r: %s", query, exc)
        return []

    results = []
    for item in data.get("data", []) or []:
        attrs = item.get("attributes", {}) or {}
        titles = attrs.get("titles") or []
        title = titles[0].get("title") if titles else "Untitled dataset"
        descriptions = attrs.get("descriptions") or []
        description = descriptions[0].get("description") if descriptions else "No description provided by the repository."
        doi = attrs.get("doi")
        results.append({
            "name": title,
            "repository": (attrs.get("publisher") or "DataCite"),
            "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else None,
            "description": (description or "")[:600],
        })
    return results
