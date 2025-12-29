from dataclasses import dataclass
from typing import List, Tuple

from ..utils.config import RISK_KEYWORDS
from ..utils.text import find_keywords


@dataclass
class ClassificationResult:
    kind: str
    complexity: int
    confidence: float
    risk_flags: List[str]


KIND_RULES: List[Tuple[str, str, int, float]] = [
    ("CC", "credit card|billing|card submit", 4, 0.9),
    ("PIN", "pin submit|sms pin|verification", 4, 0.85),
    ("INSTALL", "install|app install|apk|ios install", 3, 0.7),
    ("SURVEY", "survey|questionnaire|quiz", 2, 0.6),
    ("DOI", "double opt|confirm email|doi", 3, 0.6),
    ("SOI", "email submit|zip submit|single opt|soi|zip", 2, 0.5),
]


PRIORITY_ORDER = ["CC", "PIN", "INSTALL", "SURVEY", "DOI", "SOI", "UNKNOWN"]


def classify_offer(text: str, offer_type: str | None = None) -> ClassificationResult:
    text_lower = text.lower()
    matched_kind = "UNKNOWN"
    matched_confidence = 0.3
    matched_complexity = 3
    matched_index = PRIORITY_ORDER.index("UNKNOWN")

    for idx, (kind, pattern, complexity, confidence) in enumerate(KIND_RULES):
        tokens = pattern.split("|")
        if any(token in text_lower for token in tokens) or (
            offer_type and kind.lower() in offer_type.lower()
        ):
            if idx <= matched_index:
                matched_kind = kind
                matched_confidence = confidence
                matched_complexity = complexity
                matched_index = idx
            if kind in {"CC", "PIN"}:
                break

    risk_flags = find_keywords(text, RISK_KEYWORDS)
    return ClassificationResult(
        kind=matched_kind,
        complexity=matched_complexity,
        confidence=matched_confidence,
        risk_flags=risk_flags,
    )
