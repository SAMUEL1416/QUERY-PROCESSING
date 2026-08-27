"""
Searches the real UCI Machine Learning Repository public API.
Endpoints (used by the official `ucimlrepo` package):
  - List/search: https://archive.ics.uci.edu/api/datasets/list?search=<q>
  - Detail:      https://archive.ics.uci.edu/api/dataset?id=<id>
No authentication required.
"""
import logging
from typing import List

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

LIST_URL = "https://archive.ics.uci.edu/api/datasets/list"
DETAIL_URL = "https://archive.ics.uci.edu/api/dataset"


def search(query: str, limit: int = 5) -> List[dict]:
    settings = get_settings()
    try:
        resp = requests.get(
            LIST_URL,
            params={"search": query},
            timeout=settings.external_api_timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        logger.warning("UCI dataset search failed for %r: %s", query, exc)
        return []
    except ValueError as exc:
        logger.warning("UCI dataset search returned invalid JSON for %r: %s", query, exc)
        return []

    if payload.get("status") != 200:
        return []

    items = (payload.get("data") or [])[:limit]
    results = []
    for item in items:
        uci_id = item.get("id")
        name = item.get("name", "Untitled dataset")
        results.append({
            "name": name,
            "repository": "UCI Machine Learning Repository",
            "doi": None,
            "url": f"https://archive.ics.uci.edu/dataset/{uci_id}" if uci_id else "https://archive.ics.uci.edu/",
            "description": item.get("abstract") or item.get("description") or "No description provided by the repository.",
        })
    return results


def get_detail(uci_id: int) -> dict | None:
    settings = get_settings()
    try:
        resp = requests.get(DETAIL_URL, params={"id": uci_id}, timeout=settings.external_api_timeout)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("UCI dataset detail fetch failed for id=%s: %s", uci_id, exc)
        return None
    if payload.get("status") != 200:
        return None
    return payload.get("data")
