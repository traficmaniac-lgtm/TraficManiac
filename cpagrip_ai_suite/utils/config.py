import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "user_id": "2482254",
    "private_key": "55945b018809d7d701d085456db133ba",
    "tracking_id": "${SUBID}",
    "limit": 100,
    "showall": 1,
    "country": "",
    "offer_type": "",
    "domain": "",
    "showmobile": 1,
    "ai_top_n": 50,
    "max_complexity": 3,
    "sort_by": "profit_score",
}

GEO_TIERS = {
    "tier1": {
        "countries": {"US", "GB", "CA", "AU", "NZ", "DE", "FR"},
        "weight": 1.3,
    },
    "tier2": {
        "countries": {"IT", "ES", "PT", "NL", "BE", "SE", "NO", "FI", "DK"},
        "weight": 1.1,
    },
    "tier3": {
        "countries": set(),
        "weight": 1.0,
    },
}

DESCRIPTION_TRIM = 220

# Path to store user-overridable settings such as OpenAI credentials.

APP_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


def load_app_config() -> dict:
    """Load persisted application config if it exists."""
    if APP_CONFIG_PATH.exists():
        try:
            with APP_CONFIG_PATH.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            # Ignore malformed user files; the UI will allow re-saving
            return {}
    return {}


def save_app_config(payload: dict) -> None:
    """Persist user settings (e.g., OpenAI API options) to disk."""
    APP_CONFIG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
