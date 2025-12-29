import json

from ..core.offer_model import OfferNormalized


PROP_TEMPLATE = {
    "campaign_name": "",
    "format": "push",
    "frequency_cap": "",  # e.g., 3 per 24h
    "traffic_sources": "propeller_ads",
    "bids": {
        "geo": [],
        "cpc": "",
    },
    "targeting": {
        "device": "all",
        "os": "all",
        "zones_to_exclude": [],
        "subzone_rules": [],
    },
    "schedule": "",
    "creatives": [],
    "economics": {
        "ctr_expectation": "",
        "cr_expectation": "",
        "breakeven_cpc": "",
        "roi_scenarios": "",
        "stop_conditions": "",
    },
}


def build_propeller_campaign_prompt(offer: OfferNormalized, test_budget: float) -> str:
    payload = {
        "instruction": "Return STRICT JSON following the template for PropellerAds push campaign.",
        "offer": {
            "offer_id": offer.offer_id,
            "title": offer.title,
            "payout": offer.payout,
            "geo": offer.geo_list,
            "kind": offer.kind,
            "complexity": offer.complexity,
            "risk_flags": offer.risk_flags,
            "profit_score": offer.profit_score,
        },
        "test_budget": test_budget,
        "campaign_template": PROP_TEMPLATE,
    }
    notes = "Fill all placeholder fields and keep JSON valid."
    return notes + "\n" + json.dumps(payload, indent=2)
