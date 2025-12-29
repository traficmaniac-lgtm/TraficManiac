from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

TIER1 = {"US", "CA", "UK", "GB", "AU", "DE", "FR"}


@dataclass
class OfferScore:
    score: float
    notes: str
    breakdown: List[Tuple[str, float]]
    risk_level: str
    risk_reason: str
    risk_flag: bool


def _conversion_bonus(conversion_type: str | None) -> float:
    if not conversion_type:
        return 0.0
    conv = conversion_type.lower()
    if any(key in conv for key in ["soi", "email", "submit", "app"]):
        return 0.25
    if "doi" in conv or "double" in conv:
        return 0.12
    if "pin" in conv:
        return -0.08
    return 0.0


def _traffic_penalty(forbidden: List[str]) -> float:
    text = " ".join(forbidden).lower()
    penalty = 0.0
    if any(key in text for key in ["brand", "trademark", "bidding"]):
        penalty -= 0.1
    if any(key in text for key in ["adult not", "no adult", "gambling", "vpn", "proxy"]):
        penalty -= 0.08
    return penalty


def _epc_bonus(epc: float | None, cr: float | None) -> float:
    bonus = 0.0
    if epc:
        bonus += min(epc, 3.0) * 0.1
    if cr:
        bonus += min(cr, 5.0) * 0.05
    return bonus


def _risk_level_from_title(title: str, conversion_type: str | None) -> tuple[str, str]:
    text = title.lower()
    conv = (conversion_type or "").lower()
    if any(brand in text for brand in ["amazon", "apple", "walmart"]):
        return "high", "Contains sensitive brand terms"
    if "gift card" in text:
        return "medium", "Generic gift card offer"
    if any(key in text for key in ["opera gx", "app install"]) or any(
        key in conv for key in ["email", "submit", "app"]
    ):
        return "low", "Email/App style flow"
    return "medium", "Standard flow"


def score_offer(
    payout_usd: float,
    conversion_type: str | None,
    geo_allowed: List[str],
    offer_title: str,
    epc: float | None,
    cr: float | None,
    incentive_allowed: bool | None,
    traffic_forbidden: List[str],
    cap: float | None,
) -> OfferScore:
    notes: List[str] = []
    breakdown: List[Tuple[str, float]] = []
    score = 0.0

    payout_component = max(payout_usd * 0.35, 0)
    breakdown.append(("Payout weight", round(payout_component, 2)))
    score += payout_component

    conversion_gain = _conversion_bonus(conversion_type)
    conversion_component = payout_usd * conversion_gain
    breakdown.append(("Conversion simplicity", round(conversion_component, 2)))
    score += conversion_component

    if any(geo in TIER1 for geo in geo_allowed):
        tier_bonus = payout_usd * 0.25
        breakdown.append(("GEO tier boost", round(tier_bonus, 2)))
        score += tier_bonus

    extra = _epc_bonus(epc, cr)
    if extra:
        breakdown.append(("EPC/CR support", round(extra, 2)))
        score += extra
    else:
        breakdown.append(("Missing EPC", -0.2))
        score -= 0.2

    if incentive_allowed is False and conversion_type and "pin" in conversion_type.lower():
        pin_penalty = payout_usd * 0.12
        breakdown.append(("Incentive off + PIN", round(-pin_penalty, 2)))
        score -= pin_penalty

    traffic_penalty = _traffic_penalty(traffic_forbidden)
    if traffic_penalty:
        penalty_value = payout_usd * abs(traffic_penalty)
        breakdown.append(("Traffic restrictions", round(-penalty_value, 2)))
        score += payout_usd * traffic_penalty

    if cap is None:
        breakdown.append(("No cap info", -0.1))
        score -= 0.1
    elif cap < 20:
        cap_penalty = payout_usd * 0.2
        breakdown.append(("Cap too low", round(-cap_penalty, 2)))
        score -= cap_penalty

    risk_level, risk_reason = _risk_level_from_title(offer_title, conversion_type)

    risk_flag = risk_level == "high"
    notes.extend(f"{name}={value:+}" for name, value in breakdown)

    return OfferScore(
        score=round(score, 3),
        notes="; ".join(notes),
        breakdown=breakdown,
        risk_level=risk_level,
        risk_reason=risk_reason,
        risk_flag=risk_flag,
    )
