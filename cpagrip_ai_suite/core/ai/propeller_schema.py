from __future__ import annotations

PROP_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "PropellerSettingsSchema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "campaign_name",
        "format",
        "pricing_model",
        "geo",
        "language",
        "platform",
        "os",
        "device",
        "browser",
        "connection",
        "vpn_proxy",
        "traffic_quality",
        "schedule",
        "caps",
        "bidding",
        "tracking",
        "test_plan",
        "creatives",
        "risk_check",
    ],
    "properties": {
        "campaign_name": {"type": "string", "minLength": 1},
        "format": {"type": "string", "enum": ["inpage_push", "classic_push"]},
        "pricing_model": {"type": "string", "enum": ["cpc", "cpm"]},
        "geo": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "language": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "platform": {"type": "string", "enum": ["mobile", "desktop", "all"]},
        "os": {"type": "array", "items": {"type": "string"}},
        "device": {"type": "array", "items": {"type": "string"}},
        "browser": {"type": "array", "items": {"type": "string"}},
        "connection": {"type": "array", "items": {"type": "string"}},
        "vpn_proxy": {"type": "string", "enum": ["exclude", "allow"]},
        "traffic_quality": {"type": "string", "enum": ["hq", "all"]},
        "schedule": {
            "type": "object",
            "additionalProperties": False,
            "required": ["days", "time_windows_local"],
            "properties": {
                "days": {"type": "array", "items": {"type": "string"}},
                "time_windows_local": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {"type": "string", "pattern": "^\\d{2}:\\d{2}$"},
                    },
                },
            },
        },
        "caps": {
            "type": "object",
            "additionalProperties": False,
            "required": ["daily_budget_usd", "total_budget_usd", "frequency_cap"],
            "properties": {
                "daily_budget_usd": {"type": "number"},
                "total_budget_usd": {"type": "number"},
                "frequency_cap": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["clicks", "hours"],
                    "properties": {
                        "clicks": {"type": "integer", "minimum": 0},
                        "hours": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
        "bidding": {
            "type": "object",
            "additionalProperties": False,
            "required": ["start_bid", "max_bid", "bid_adjust_rules"],
            "properties": {
                "start_bid": {"type": "number"},
                "max_bid": {"type": "number"},
                "bid_adjust_rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["condition", "action"],
                        "properties": {
                            "condition": {"type": "string"},
                            "action": {"type": "string"},
                            "value": {"type": ["number", "string", "null"]},
                        },
                    },
                },
            },
        },
        "tracking": {
            "type": "object",
            "additionalProperties": False,
            "required": ["final_url", "macros"],
            "properties": {
                "final_url": {"type": "string"},
                "macros": {"type": "array", "items": {"type": "string"}},
            },
        },
        "test_plan": {
            "type": "object",
            "additionalProperties": False,
            "required": ["day1_goal_clicks", "stop_rules"],
            "properties": {
                "day1_goal_clicks": {"type": "integer", "minimum": 1},
                "stop_rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["condition", "action"],
                        "properties": {
                            "condition": {"type": "string"},
                            "action": {"type": "string"},
                        },
                    },
                },
            },
        },
        "creatives": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "text", "icon_guidance"],
                "properties": {
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "icon_guidance": {"type": "string"},
                },
            },
        },
        "risk_check": {
            "type": "object",
            "additionalProperties": False,
            "required": ["risk_level", "ban_triggers", "mitigations"],
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "ban_triggers": {"type": "array", "items": {"type": "string"}},
                "mitigations": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}
