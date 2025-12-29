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
