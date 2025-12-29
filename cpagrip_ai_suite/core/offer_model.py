from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from .offer_classifier import classify_offer
from .scoring import calculate_profit_score
from ..utils.config import DESCRIPTION_TRIM
from ..utils.geo import detect_geo_tier, geo_weight
from ..utils.text import extract_geo_list, truncate


@dataclass
class OfferNormalized:
    offer_id: str
    title: str
    payout: float
    geo_raw: str
    geo_list: List[str]
    offerlink: str
    description_short: str
    restrictions_short: str
    allowed_traffic_short: str
    kind: str
    complexity: int
    geo_tier: str
    geo_weight: float
    risk_flags: List[str]
    profit_score: float
    score_explain: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OfferNormalizationResult:
    offers: List[OfferNormalized]
    errors: List[str]


def normalize_offer(raw: Dict[str, Any]) -> OfferNormalized:
    offer_id = str(raw.get("id", "") or "")
    title = raw.get("title", "Untitled Offer")
    payout = float(raw.get("payout", 0.0) or 0.0)
    geo_raw = raw.get("countries", "")
    geo_list = extract_geo_list(geo_raw)
    offerlink = raw.get("offerlink", "")
    desc = raw.get("description", "")
    restrictions = raw.get("restrictions", raw.get("allowed_countries", ""))
    allowed_traffic = raw.get("allowed_traffic", raw.get("traffic_source", ""))

    text_for_classification = " ".join([title, desc, raw.get("type", ""), raw.get("offer_type", "")])
    classification = classify_offer(text_for_classification, offer_type=raw.get("type", ""))
    geo_tier = detect_geo_tier(geo_list)
    score = calculate_profit_score(
        payout=payout,
        tier=geo_tier,
        complexity=classification.complexity,
        risk_flags=classification.risk_flags,
        kind=classification.kind,
    )

    return OfferNormalized(
        offer_id=offer_id,
        title=title,
        payout=payout,
        geo_raw=geo_raw,
        geo_list=geo_list,
        offerlink=offerlink,
        description_short=truncate(desc, DESCRIPTION_TRIM),
        restrictions_short=truncate(restrictions, DESCRIPTION_TRIM),
        allowed_traffic_short=truncate(allowed_traffic, DESCRIPTION_TRIM),
        kind=classification.kind,
        complexity=classification.complexity,
        geo_tier=geo_tier,
        geo_weight=geo_weight(geo_tier),
        risk_flags=classification.risk_flags,
        profit_score=score.profit_score,
        score_explain=score.explanation,
        confidence=classification.confidence,
    )


def normalize_offers(raw_offers: List[Dict[str, Any]]) -> OfferNormalizationResult:
    normalized = []
    errors = []
    for item in raw_offers:
        try:
            normalized.append(normalize_offer(item))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to normalize offer {item.get('id', '')}: {exc}")
    return OfferNormalizationResult(offers=normalized, errors=errors)
