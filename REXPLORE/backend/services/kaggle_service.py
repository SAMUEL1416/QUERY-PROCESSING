"""
Searches the real Kaggle Datasets API.
Docs: https://github.com/Kaggle/kaggle-api (REST endpoint used by the CLI/SDK)
  GET https://www.kaggle.com/api/v1/datasets/list?search=<query>
Requires a Kaggle account's API credentials (username + key from
https://www.kaggle.com/settings -> "Create New Token"). Without credentials
configured, this service is skipped entirely rather than faking results.
"""
import logging
from typing import List

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kaggle.com/api/v1/datasets/list"


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.kaggle_username and settings.kaggle_key)


def search(query: str, limit: int = 5) -> List[dict]:
    settings = get_settings()
    if not is_configured():
        logger.info("Kaggle credentials not configured; skipping Kaggle search.")
        return []
    try:
        resp = requests.get(
            BASE_URL,
            params={"search": query, "pageSize": limit},
            auth=(settings.kaggle_username, settings.kaggle_key),
            timeout=settings.external_api_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Kaggle dataset search failed for %r: %s", query, exc)
        return []
    except ValueError as exc:
        logger.warning("Kaggle dataset search returned invalid JSON for %r: %s", query, exc)
        return []

    results = []
    for item in (data or [])[:limit]:
        ref = item.get("ref")  # e.g. "owner/dataset-slug"
        results.append({
            "name": item.get("title") or ref or "Untitled dataset",
            "repository": "Kaggle",
            "doi": None,
            "url": f"https://www.kaggle.com/datasets/{ref}" if ref else "https://www.kaggle.com/datasets",
            "description": item.get("subtitle") or "No description provided by the repository.",
        })
    return results
