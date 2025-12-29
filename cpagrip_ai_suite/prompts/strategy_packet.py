from __future__ import annotations

import json
from typing import Dict

from ..core.offer_model import OfferNormalized


def build_strategy_packet(offer: OfferNormalized) -> str:
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
