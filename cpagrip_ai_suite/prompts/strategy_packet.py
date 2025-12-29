from __future__ import annotations

import json
 codex/update-cpagrip-offer-aggregator-ojcgo1
from typing import Dict

from typing import Dict, List, Tuple
 main

from ..core.offer_model import OfferNormalized


 codex/update-cpagrip-offer-aggregator-ojcgo1
def build_strategy_packet(offer: OfferNormalized) -> str:

def _best_format(traffic_allowed: List[str], lp_type_guess: str | None) -> str:
    text = " ".join(traffic_allowed).lower()
    if "inpage" in text:
        return "inpage_push"
    if "push" in text:
        return "push"
    if lp_type_guess and "smartlink" in lp_type_guess:
        return "inpage_push"
    return "inpage_push"


def _best_device(devices: List[str]) -> str:
    text = " ".join(devices).lower()
    if any(key in text for key in ["android", "android_mobile", "mobile"]):
        return "android_mobile"
    if "ios" in text:
        return "ios_mobile"
    if "desktop" in text or "windows" in text:
        return "desktop"
    return "android_mobile"


def _expected_ranges(payout_usd: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    base_cpc = max(min(payout_usd * 0.02, 0.04), 0.01)
    cpc_range = (round(base_cpc * 0.75, 3), round(base_cpc * 1.25, 3))
    cr_base = 0.6 if payout_usd < 3 else 0.8
    cr_range = (round(cr_base, 1), round(cr_base * 1.6, 1))
    return cpc_range, cr_range


def build_strategy_packet(offer: OfferNormalized) -> str:
    cpc_range, cr_range = _expected_ranges(offer.payout_usd)
    best_format = _best_format(offer.traffic_allowed, offer.lp_type_guess)
    best_device = _best_device(offer.devices)
    breakeven_clicks = max(int((offer.payout_usd / max(offer.epc or 0.18, 0.18)) * 0.6), 120)
    initial_clicks = max(breakeven_clicks * 2, 300)
 main
    packet: Dict[str, object] = {
        "task": "build_profitable_strategy",
        "traffic_source": "PropellerAds",
        "network": "CPAGrip",
        "offer": offer.to_strategy_offer(),
        "tracking": {
            "required_macros": ["${SUBID}", "${ZONEID}", "${OS}", "${BROWSER}", "${DEVICE}"],
            "final_url_example": offer.tracking_url.replace("${SUBID}", "{subid}"),
        },
        "constraints": {
            "test_budget_usd": 30,
            "goal": "profit_fast_and_safe",
            "ban_risk_priority": "high",
        },
 codex/update-cpagrip-offer-aggregator-ojcgo1

        "recommendations": {
            "best_format_guess": best_format,
            "best_device_guess": best_device,
            "expected_cpc_range": cpc_range,
            "expected_cr_range": cr_range,
            "breakeven_clicks_estimate": breakeven_clicks,
            "initial_test_clicks": initial_clicks,
        },
 main
        "context": {
            "geo_timezone": "Europe/Kyiv",
            "language": "ru",
            "experience_level": "advanced",
        },
        "questions_for_ai": [
            "Выдай точные настройки кампании PropellerAds (format, bid, caps, schedule, targeting, exclusions).",
            "Сделай план теста на $30: сколько зон, какие ставки, стоп-лоссы, когда резать/масштабировать.",
            "Предложи 3-5 креативов и текстов (push/inpage) и требования к баннерам (размеры).",
            "Дай risk-check: что может баниться и как снизить риск.",
        ],
    }
    return json.dumps(packet, ensure_ascii=False, indent=2)
