from typing import List

from .config import GEO_TIERS


def detect_geo_tier(geo_list: List[str]) -> str:
    if not geo_list:
        return "mixed"
    tiers = set()
    for code in geo_list:
        if code in GEO_TIERS["tier1"]["countries"]:
            tiers.add("tier1")
        elif code in GEO_TIERS["tier2"]["countries"]:
            tiers.add("tier2")
        else:
            tiers.add("tier3")
    if len(tiers) == 1:
        return tiers.pop()
    return "mixed"


def geo_weight(tier: str) -> float:
    if tier in GEO_TIERS:
        return GEO_TIERS[tier]["weight"]
    return 1.0
