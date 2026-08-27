"""
Detects candidate dataset names mentioned anywhere in the full paper text.
Thin, purpose-named wrapper around feature_extractor's dataset-mention
heuristic, with light de-duplication/cleanup for use as search queries.
"""
from typing import List

from services.feature_extractor import extract_dataset_mentions


def detect_dataset_names(full_text: str, pages) -> List[str]:
    features = extract_dataset_mentions(full_text, pages)
    names = []
    seen = set()
    for f in features:
        cleaned = f.value.strip()
        key = cleaned.lower()
        if key in seen or len(cleaned) < 3:
            continue
        seen.add(key)
        names.append(cleaned)
    return names
