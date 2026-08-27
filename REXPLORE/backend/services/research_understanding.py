"""
Builds the study-friendly "Research Understanding" output for a paper:
for each detected section -> key points, a short extractive explanation,
concepts, and findings. Everything here is extractive (derived only from
text present in the section) - nothing is generated/fabricated.
"""
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List

from services.section_extractor import DetectedSection

NOT_IDENTIFIED = "Not identified in the available paper content."

FINDING_TRIGGER_WORDS = [
    "we found", "we show", "results show", "our results", "demonstrate", "achieves",
    "outperform", "improv", "significant", "we observe", "indicate that", "reveal",
]


def _split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Basic sentence splitter (avoids heavy NLP deps); good enough for extractive scoring.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def _score_sentences(sentences: List[str]) -> List[float]:
    words = re.findall(r"[a-z]{4,}", " ".join(sentences).lower())
    freq = Counter(words)
    scores = []
    for i, s in enumerate(sentences):
        sw = re.findall(r"[a-z]{4,}", s.lower())
        score = sum(freq[w] for w in sw) / (len(sw) + 1)
        # Slight boost for earlier sentences (topic sentences) and first sentence overall
        position_boost = 1.15 if i == 0 else 1.0
        scores.append(score * position_boost)
    return scores


@dataclass
class SectionUnderstanding:
    name: str
    page_number: int
    order_index: int
    raw_text: str
    key_points: List[str] = field(default_factory=list)
    simple_explanation: str = ""
    concepts: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


def _key_points_for(sentences: List[str], scores: List[float], max_points: int = 4) -> List[str]:
    if not sentences:
        return [NOT_IDENTIFIED]
    ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
    top_idx = sorted(ranked[:max_points])  # keep original order for readability
    return [sentences[i] for i in top_idx]


def _simple_explanation_for(sentences: List[str], scores: List[float]) -> str:
    if not sentences:
        return NOT_IDENTIFIED
    best_idx = max(range(len(sentences)), key=lambda i: scores[i])
    # Use the strongest sentence plus the following one (if present) for a short,
    # coherent 2-sentence explanation.
    picks = [sentences[best_idx]]
    if best_idx + 1 < len(sentences) and len(picks[0]) < 220:
        picks.append(sentences[best_idx + 1])
    return " ".join(picks)


def _findings_for(sentences: List[str]) -> List[str]:
    findings = [
        s for s in sentences
        if any(trigger in s.lower() for trigger in FINDING_TRIGGER_WORDS)
    ]
    return findings[:5] if findings else [NOT_IDENTIFIED]


def _concepts_for_section(section_text: str, global_concepts: List[str], max_concepts: int = 8) -> List[str]:
    text_lower = section_text.lower()
    present = [c for c in global_concepts if c in text_lower]
    return present[:max_concepts] if present else [NOT_IDENTIFIED]


def build_section_understanding(
    sections: List[DetectedSection], global_concepts: List[str]
) -> List[SectionUnderstanding]:
    results = []
    for sec in sections:
        sentences = _split_sentences(sec.raw_text)
        scores = _score_sentences(sentences)
        results.append(
            SectionUnderstanding(
                name=sec.name,
                page_number=sec.page_number,
                order_index=sec.order_index,
                raw_text=sec.raw_text,
                key_points=_key_points_for(sentences, scores),
                simple_explanation=_simple_explanation_for(sentences, scores),
                concepts=_concepts_for_section(sec.raw_text, global_concepts),
                findings=_findings_for(sentences),
            )
        )
    return results


def infer_research_domain(full_text: str, algorithms: List[str], concepts: List[str]) -> str:
    """
    Lightweight, transparent domain inference from vocabulary overlap with
    common research-domain indicator terms actually present in the text.
    Returns NOT_IDENTIFIED if nothing matches (never guesses blindly).
    """
    domain_indicators = {
        "Natural Language Processing": ["nlp", "language model", "text classification", "sentiment", "tokeniz", "corpus", "translation"],
        "Computer Vision": ["image", "cnn", "convolutional", "object detection", "segmentation", "pixel", "vision"],
        "Machine Learning": ["classification", "regression", "supervised", "unsupervised", "training set", "feature"],
        "Healthcare / Medical Informatics": ["patient", "clinical", "diagnosis", "medical", "disease", "healthcare"],
        "Cybersecurity": ["intrusion", "malware", "attack", "vulnerability", "encryption", "security"],
        "Bioinformatics": ["gene", "genome", "protein", "dna", "sequence alignment"],
        "Robotics": ["robot", "actuator", "kinematics", "trajectory planning"],
        "Recommender Systems": ["recommend", "collaborative filtering", "user-item"],
    }
    text_lower = full_text.lower()
    scores = {}
    for domain, indicators in domain_indicators.items():
        score = sum(text_lower.count(term) for term in indicators)
        if score > 0:
            scores[domain] = score
    if not scores:
        return NOT_IDENTIFIED
    return max(scores, key=scores.get)
