from __future__ import annotations

from typing import Dict, List

from .propeller_schema import PROP_SCHEMA


SYSTEM_PROMPT = (
    "Ты senior CPA медиабаер. Верни ТОЛЬКО JSON, соответствующий схеме PropellerSettingsSchema. "
    "Учитывай constraints: budget_total_usd=30, ban_risk_priority=high. Если данных мало — делай безопасные "
    "допущения, но не пропускай поля."
)


def build_messages(ai_packet: Dict[str, object], validation_errors: List[str] | None = None) -> List[Dict[str, str]]:
    user_content = ai_packet
    if validation_errors:
        user_content = {
            "ai_packet": ai_packet,
            "fix_to_schema": validation_errors,
        }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


__all__ = ["SYSTEM_PROMPT", "PROP_SCHEMA", "build_messages"]
