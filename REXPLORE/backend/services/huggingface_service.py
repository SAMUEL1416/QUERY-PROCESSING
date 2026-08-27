"""
Searches the real Hugging Face Datasets Hub public API.
Docs: https://huggingface.co/docs/hub/api#get-apidatasets
No authentication required for public dataset search.
"""
import logging
from typing import List, Optional

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

BASE_URL = "https://huggingface.co/api/datasets"


def search(query: str, limit: int = 5) -> List[dict]:
    settings = get_settings()
    try:
        resp = requests.get(
            BASE_URL,
            params={"search": query, "limit": limit, "full": "true"},
            timeout=settings.external_api_timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Hugging Face dataset search failed for %r: %s", query, exc)
        return []
    except ValueError as exc:
        logger.warning("Hugging Face dataset search returned invalid JSON for %r: %s", query, exc)
        return []

    results = []
    for item in data or []:
        dataset_id = item.get("id")
        if not dataset_id:
            continue
        card = item.get("cardData") or {}
        results.append({
            "name": dataset_id,
            "repository": "Hugging Face Datasets",
            "doi": None,
            "url": f"https://huggingface.co/datasets/{dataset_id}",
            "description": card.get("summary") or item.get("description") or "No description provided by the repository.",
        })
    return results
