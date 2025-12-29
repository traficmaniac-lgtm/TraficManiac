import json
from typing import Iterable

from ..core.offer_model import OfferNormalized


PROMPT_HEADER = "You are a media buying assistant. Return STRICT JSON only."


def compact_offer(card: OfferNormalized) -> dict:
    return {
        "offer_id": card.offer_id,
        "title": card.title,
        "payout": card.payout,
        "geo": card.geo_list,
        "kind": card.kind,
        "complexity": card.complexity,
        "profit_score": card.profit_score,
        "risk_flags": card.risk_flags,
    }


def build_ai_selection_prompt(cards: Iterable[OfferNormalized], budget: float, traffic_source: str = "PropellerAds") -> str:
    serialized_cards = [compact_offer(card) for card in cards]
    payload = {
        "instruction": PROMPT_HEADER,
        "budget": budget,
        "traffic_source": traffic_source,
        "offers": serialized_cards,
        "expected_response": {
            "top10": [
                {
                    "offer_id": "",
                    "title": "",
                    "why": "",
                    "recommended_format": "",
                    "recommended_geo": [],
                    "risk_level": "",
                    "quick_test_plan": "",
                }
                for _ in range(10)
            ],
            "top3_propeller_campaigns": [
                {
                    "offer_id": "",
                    "campaign": {
                        "name": "",
                        "format": "push",
                        "geo": [],
                        "cpc_bid": "",
                        "frequency_cap": "",
                        "targeting": "",
                        "notes": "",
                    },
                }
                for _ in range(3)
            ],
            "global_notes": {
                "assumptions": "",
                "red_flags": [],
                "next_data_to_collect": [],
            },
        },
    }
    prompt = (
        "You MUST respond strictly with JSON matching this shape. "
        "Pick top offers for the given budget."
    )
    return prompt + "\n" + json.dumps(payload, indent=2)
