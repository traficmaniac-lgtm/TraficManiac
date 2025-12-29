from __future__ import annotations

from dataclasses import dataclass
from typing import List

TIER1 = {"US", "CA", "UK", "GB", "AU", "DE", "FR"}


@dataclass
class OfferScore:
    score: float
    notes: str
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


def score_offer(
    payout_usd: float,
    conversion_type: str | None,
    geo_allowed: List[str],
    epc: float | None,
    cr: float | None,
    incentive_allowed: bool | None,
    traffic_forbidden: List[str],
    cap: float | None,
) -> OfferScore:
    notes: List[str] = []
    score = payout_usd
    notes.append(f"base payout={payout_usd}")

    conversion_gain = _conversion_bonus(conversion_type)
    score += payout_usd * conversion_gain
    notes.append(f"conversion bonus={conversion_gain:.2f}")

    if any(geo in TIER1 for geo in geo_allowed):
        tier_bonus = 0.15 * payout_usd
        score += tier_bonus
        notes.append(f"tier1 bonus={tier_bonus:.2f}")

    extra = _epc_bonus(epc, cr)
    score += extra
    if extra:
        notes.append(f"epc/cr bonus={extra:.2f}")

    if incentive_allowed is False and conversion_type and "pin" in conversion_type.lower():
        score -= payout_usd * 0.12
        notes.append("incentive off + pin penalty")

    traffic_penalty = _traffic_penalty(traffic_forbidden)
    score += payout_usd * traffic_penalty
    if traffic_penalty:
        notes.append(f"traffic penalty factor={traffic_penalty:.2f}")

    if cap is not None and cap < 20:
        score -= payout_usd * 0.2
        notes.append("cap too low penalty")

    risk_flag = (incentive_allowed is False) or any(
        key in " ".join(traffic_forbidden).lower()
        for key in ["brand", "trademark", "adult", "gambling", "vpn", "proxy"]
    )

    return OfferScore(score=round(score, 3), notes="; ".join(notes), risk_flag=risk_flag)
