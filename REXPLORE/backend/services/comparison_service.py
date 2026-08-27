"""
Builds a side-by-side comparison of multiple papers across the standard
research dimensions, pulling only from what was actually extracted and
stored for each paper. Missing information is reported as "Not identified."
"""
from typing import List

from sqlalchemy.orm import Session

from app import models

NOT_IDENTIFIED = "Not identified."

# Canonical section names (from section_extractor) mapped to comparison dimensions.
DIMENSION_SECTION_MAP = {
    "Problem": ["Problem Statement"],
    "Research Gap": ["Research Gap"],
    "Objective": ["Objectives"],
    "Methodology": ["Methodology", "Method", "Proposed Method", "Proposed Approach"],
    "Results": ["Results", "Experiments"],
    "Limitations": ["Limitations"],
    "Future Work": ["Future Work"],
}


def _first_matching_section_summary(sections: List[models.PaperSection], names: List[str]) -> str:
    for sec in sections:
        if sec.name in names:
            if sec.key_points:
                return " ".join(sec.key_points[:2])
            if sec.simple_explanation:
                return sec.simple_explanation
    return NOT_IDENTIFIED


def compare_papers(db: Session, paper_ids: List[int], user_id: int) -> List[dict]:
    results = []
    for pid in paper_ids:
        paper = (
            db.query(models.Paper)
            .filter(models.Paper.id == pid, models.Paper.user_id == user_id)
            .first()
        )
        if not paper:
            results.append({"paper_id": pid, "error": "Paper not found"})
            continue

        sections = paper.sections
        features = paper.features

        algorithms = sorted({f.value for f in features if f.feature_type == "algorithm"})
        datasets = sorted({f.value for f in features if f.feature_type == "dataset"})
        metrics = sorted({f.value for f in features if f.feature_type == "metric"})

        row = {
            "paper_id": pid,
            "title": paper.title or paper.original_filename,
            "Problem": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Problem"]),
            "Research Gap": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Research Gap"]),
            "Objective": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Objective"]),
            "Methodology": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Methodology"]),
            "Algorithms": ", ".join(algorithms) if algorithms else NOT_IDENTIFIED,
            "Datasets": ", ".join(datasets) if datasets else NOT_IDENTIFIED,
            "Metrics": ", ".join(metrics) if metrics else NOT_IDENTIFIED,
            "Results": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Results"]),
            "Limitations": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Limitations"]),
            "Future Work": _first_matching_section_summary(sections, DIMENSION_SECTION_MAP["Future Work"]),
        }
        results.append(row)
    return results
