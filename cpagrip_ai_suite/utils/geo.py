from __future__ import annotations

from typing import List

from .config import GEO_TIERS
from .text import extract_geo_list


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


def normalize_country_codes(codes: List[str]) -> List[str]:
    cleaned = [code.strip().upper() for code in codes if code]
    unique: List[str] = []
    for code in cleaned:
        if code not in unique:
            unique.append(code)
    return unique


def parse_geo_string(value: str) -> List[str]:
    return normalize_country_codes(extract_geo_list(value))
