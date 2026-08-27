"""
Detects standard research-paper sections from extracted page text using
heading heuristics (numbered/unnumbered headings matching a known section
vocabulary, case-insensitive, allowing common synonyms).

This does NOT invent section content: each detected section's raw_text is
exactly the text found between its heading and the next detected heading.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from services.pdf_processor import PageText

# Canonical section name -> accepted heading synonyms (regex-safe, lowercase)
SECTION_VOCABULARY = {
    "Abstract": ["abstract"],
    "Introduction": ["introduction"],
    "Background": ["background"],
    "Related Work": ["related work", "related works", "prior work"],
    "Literature Review": ["literature review"],
    "Problem Statement": ["problem statement", "problem definition"],
    "Research Gap": ["research gap", "gap analysis"],
    "Objectives": ["objectives", "research objectives", "aims"],
    "Methodology": ["methodology", "materials and methods"],
    "Method": ["method"],
    "Proposed Method": ["proposed method", "proposed methodology"],
    "Proposed Approach": ["proposed approach", "proposed system", "proposed model"],
    "Architecture": ["architecture", "system architecture", "model architecture"],
    "Experiments": ["experiments", "experimental setup", "experiment"],
    "Results": ["results", "experimental results"],
    "Discussion": ["discussion"],
    "Limitations": ["limitations", "limitation", "threats to validity"],
    "Conclusion": ["conclusion", "conclusions", "concluding remarks"],
    "Future Work": ["future work", "future directions"],
    "References": ["references", "bibliography"],
}

# Build one compiled regex per canonical name.
# Matches a line that is (optionally numbered) + the synonym + nothing else
# meaningful after it (headings are short lines).
_HEADING_PATTERNS = []
for canonical, synonyms in SECTION_VOCABULARY.items():
    alt = "|".join(re.escape(s) for s in synonyms)
    pattern = re.compile(
        rf"^\s*(?:[IVXLC]+\.|\d+(?:\.\d+)*\.?)?\s*({alt})\s*$",
        re.IGNORECASE,
    )
    _HEADING_PATTERNS.append((canonical, pattern))


@dataclass
class DetectedSection:
    name: str
    page_number: int
    order_index: int
    raw_text: str = ""


def _find_heading_on_line(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None
    for canonical, pattern in _HEADING_PATTERNS:
        if pattern.match(stripped):
            return canonical
    return None


def detect_sections(pages: List[PageText]) -> List[DetectedSection]:
    """
    Scans every page's lines for known section headings, in document order.
    Text belonging to a section spans from its heading to the next detected
    heading (across pages). If no headings are found at all, the whole
    document is returned as a single "Full Text" section so nothing is lost.
    """
    headings: List[tuple] = []  # (canonical_name, page_number, line_index_global)

    all_lines: List[tuple] = []  # (page_number, line_text)
    for page in pages:
        for line in page.text.split("\n"):
            all_lines.append((page.page_number, line))

    for idx, (page_number, line) in enumerate(all_lines):
        heading = _find_heading_on_line(line)
        if heading:
            headings.append((heading, page_number, idx))

    if not headings:
        full = "\n".join(l for _, l in all_lines).strip()
        if not full:
            return []
        return [DetectedSection(name="Full Text", page_number=pages[0].page_number if pages else 1,
                                 order_index=0, raw_text=full)]

    sections: List[DetectedSection] = []
    for i, (name, page_number, line_idx) in enumerate(headings):
        end_idx = headings[i + 1][2] if i + 1 < len(headings) else len(all_lines)
        body_lines = [l for _, l in all_lines[line_idx + 1:end_idx]]
        raw_text = "\n".join(body_lines).strip()
        sections.append(
            DetectedSection(name=name, page_number=page_number, order_index=i, raw_text=raw_text)
        )

    # Drop sections with no body text at all (heading detected but nothing followed,
    # often a false-positive short line) UNLESS it's a legitimately short section.
    sections = [s for s in sections if s.raw_text or s.name in ("Abstract",)]
    return sections
