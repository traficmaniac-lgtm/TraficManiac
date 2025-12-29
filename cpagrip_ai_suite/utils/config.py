DEFAULT_SETTINGS = {
    "user_id": "demo_user",
    "private_key": "demo_private_key",
    "tracking_id": "",
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

RISK_KEYWORDS = [
    "adult",
    "gambling",
    "crypto",
    "loan",
    "cbd",
    "dating",
    "sweepstakes",
    "incent",
    "forced",
    "bot",
    "vpn allowed",
    "vpn required",
    "brand",
    "trademark",
]

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
