from typing import Iterable, List

from .offer_model import OfferNormalized


SORT_OPTIONS = {
    "profit_score": lambda x: -x.profit_score,
    "payout": lambda x: -x.payout,
    "complexity": lambda x: x.complexity,
}


def matches_geo(geo_list: List[str], include: List[str], exclude: List[str]) -> bool:
    if include:
        if not any(code.upper() in geo_list for code in include):
            return False
    if exclude:
        if any(code.upper() in geo_list for code in exclude):
            return False
    return True


def filter_offers(
    offers: Iterable[OfferNormalized],
    search: str = "",
    include_geo: List[str] | None = None,
    exclude_geo: List[str] | None = None,
    kind: str | None = None,
    max_complexity: int | None = None,
    payout_min: float | None = None,
    payout_max: float | None = None,
    hide_risk: bool = False,
    tier_only: str | None = None,
    sort_by: str = "profit_score",
) -> List[OfferNormalized]:
    include_geo = include_geo or []
    exclude_geo = exclude_geo or []
    search_lower = search.lower()

    filtered: List[OfferNormalized] = []
    for offer in offers:
        if search_lower and search_lower not in offer.title.lower() and search_lower not in offer.geo_raw.lower():
            continue
        if not matches_geo(offer.geo_list, include_geo, exclude_geo):
            continue
        if kind and kind != "any" and offer.kind != kind:
            continue
        if max_complexity and offer.complexity > max_complexity:
            continue
        if payout_min is not None and offer.payout < payout_min:
            continue
        if payout_max is not None and offer.payout > payout_max:
            continue
        if hide_risk and offer.risk_flags:
            continue
        if tier_only and tier_only != "any" and offer.geo_tier != tier_only:
            continue
        filtered.append(offer)

    sort_key = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["profit_score"])
    filtered.sort(key=sort_key)
    return filtered
