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
    epc: float | None,
    cr: float | None,
    incentive_allowed: bool | None,
    traffic_forbidden: List[str],
    cap: float | None,
    offer_title: str = "",
) -> OfferScore:
    notes: List[str] = []
    breakdown: List[Tuple[str, float]] = []
    score = payout_usd
    notes.append(f"base payout={payout_usd}")
    breakdown.append(("base", payout_usd))

    conversion_gain = _conversion_bonus(conversion_type)
    score += payout_usd * conversion_gain
    notes.append(f"conversion bonus={conversion_gain:.2f}")
    breakdown.append(("conversion", payout_usd * conversion_gain))

    if any(geo in TIER1 for geo in geo_allowed):
        tier_bonus = 0.15 * payout_usd
        score += tier_bonus
        notes.append(f"tier1 bonus={tier_bonus:.2f}")
        breakdown.append(("tier1", tier_bonus))

    extra = _epc_bonus(epc, cr)
    score += extra
    if extra:
        notes.append(f"epc/cr bonus={extra:.2f}")
        breakdown.append(("epc_cr", extra))

    if incentive_allowed is False and conversion_type and "pin" in conversion_type.lower():
        penalty = payout_usd * 0.12
        score -= penalty
        notes.append("incentive off + pin penalty")
        breakdown.append(("pin_penalty", -penalty))

    traffic_penalty = _traffic_penalty(traffic_forbidden)
    score += payout_usd * traffic_penalty
    if traffic_penalty:
        notes.append(f"traffic penalty factor={traffic_penalty:.2f}")
        breakdown.append(("traffic", payout_usd * traffic_penalty))

    if cap is not None and cap < 20:
        penalty = payout_usd * 0.2
        score -= penalty
        notes.append("cap too low penalty")
        breakdown.append(("cap", -penalty))

    risk_level, risk_reason = _risk_level_from_title(offer_title, conversion_type)
    risk_flag = risk_level == "high" or (
        (incentive_allowed is False) or any(
            key in " ".join(traffic_forbidden).lower() for key in ["brand", "trademark", "adult", "gambling", "vpn", "proxy"]
        )
    )

    return OfferScore(
        score=round(score, 3),
        notes="; ".join(notes),
        breakdown=breakdown,
        risk_level=risk_level,
        risk_reason=risk_reason,
        risk_flag=risk_flag,
    )
