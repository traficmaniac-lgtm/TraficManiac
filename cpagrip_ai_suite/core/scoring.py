from dataclasses import dataclass

from ..utils.geo import geo_weight


@dataclass
class ScoreResult:
    profit_score: float
    explanation: str


def calculate_profit_score(payout: float, tier: str, complexity: int, risk_flags: list, kind: str) -> ScoreResult:
    base = payout * geo_weight(tier) / max(complexity, 1)
    explanation_parts = [
        f"base={payout} * weight={geo_weight(tier):.2f} / complexity={complexity}",
    ]
    score = base
    if risk_flags:
        score *= 0.85
        explanation_parts.append("risk penalty 0.85x")
    if kind in {"CC", "PIN"}:
        score *= 0.75
        explanation_parts.append("CC/PIN penalty 0.75x")
    return ScoreResult(profit_score=round(score, 4), explanation="; ".join(explanation_parts))
