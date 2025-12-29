import json
import tempfile
import unittest
from pathlib import Path

from cpagrip_ai_suite.core.ai.propeller_schema import PROP_SCHEMA
from cpagrip_ai_suite.core.ai.strategy_service import StrategyService
from cpagrip_ai_suite.core.cache.strategy_cache import StrategyCache
from jsonschema import Draft202012Validator


def load_fixture(name: str) -> dict:
    path = Path(__file__).resolve().parent / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


def make_valid_strategy(language: str = "en") -> dict:
    return {
        "campaign_name": "Test",
        "format": "inpage_push",
        "pricing_model": "cpc",
        "geo": ["US"],
        "language": [language],
        "platform": "mobile",
        "os": ["android"],
        "device": ["phone"],
        "browser": ["chrome"],
        "connection": ["wifi"],
        "vpn_proxy": "exclude",
        "traffic_quality": "hq",
        "schedule": {"days": ["mon"], "time_windows_local": [["08:00", "18:00"]]},
        "caps": {"daily_budget_usd": 20, "total_budget_usd": 30, "frequency_cap": {"clicks": 1, "hours": 12}},
        "bidding": {"start_bid": 0.02, "max_bid": 0.05, "bid_adjust_rules": []},
        "tracking": {"final_url": "https://track", "macros": ["{zoneid}"]},
        "test_plan": {"day1_goal_clicks": 30, "stop_rules": [{"condition": "loss", "action": "pause"}]},
        "creatives": [
            {"title": "t1", "text": "x", "icon_guidance": "img1"},
            {"title": "t2", "text": "y", "icon_guidance": "img2"},
            {"title": "t3", "text": "z", "icon_guidance": "img3"},
        ],
        "risk_check": {"risk_level": "medium", "ban_triggers": [], "mitigations": []},
    }


class StrategySchemaTests(unittest.TestCase):
    def test_validate_schema_ok(self) -> None:
        validator = Draft202012Validator(PROP_SCHEMA)
        sample = {
            "campaign_name": "Test",
            "format": "inpage_push",
            "pricing_model": "cpc",
            "geo": ["US"],
            "language": ["en"],
            "platform": "mobile",
            "os": ["android"],
            "device": ["phone"],
            "browser": ["chrome"],
            "connection": ["wifi"],
            "vpn_proxy": "exclude",
            "traffic_quality": "hq",
            "schedule": {"days": ["mon"], "time_windows_local": [["08:00", "18:00"]]},
            "caps": {"daily_budget_usd": 20, "total_budget_usd": 30, "frequency_cap": {"clicks": 1, "hours": 12}},
            "bidding": {"start_bid": 0.02, "max_bid": 0.05, "bid_adjust_rules": []},
            "tracking": {"final_url": "https://track", "macros": ["{zoneid}"]},
            "test_plan": {"day1_goal_clicks": 30, "stop_rules": [{"condition": "loss", "action": "pause"}]},
            "creatives": [
                {"title": "t1", "text": "x", "icon_guidance": "img1"},
                {"title": "t2", "text": "y", "icon_guidance": "img2"},
                {"title": "t3", "text": "z", "icon_guidance": "img3"},
            ],
            "risk_check": {"risk_level": "medium", "ban_triggers": [], "mitigations": []},
        }
        errors = list(validator.iter_errors(sample))
        self.assertEqual(errors, [])

    def test_cache_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.json"
            cache = StrategyCache(path=cache_path)
            calls = 0
            cached_payload = make_valid_strategy()

            def ai_client(packet, validation_errors=None):
                nonlocal calls
                calls += 1
                return cached_payload

            service = StrategyService(cache=cache, ai_client=ai_client)
            packet = load_fixture("us_giftcard.json")
            first = service.generate(packet, "123")
            self.assertEqual(calls, 1)
            self.assertFalse(first.from_cache)

            second = service.generate(packet, "123")
            self.assertTrue(second.from_cache)
            self.assertEqual(calls, 1)
            self.assertEqual(second.data, cached_payload)

    def test_cache_key_includes_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.json"
            cache = StrategyCache(path=cache_path)
            calls: list[str] = []

            def ai_client(packet, validation_errors=None):
                calls.append(packet["context"]["language"])
                return make_valid_strategy(language=packet["context"]["language"])

            service = StrategyService(cache=cache, ai_client=ai_client)
            packet_one = load_fixture("us_giftcard.json")
            packet_two = json.loads(json.dumps(packet_one))
            packet_two["context"]["language"] = "de"

            first = service.generate(packet_one, "offer-1")
            second = service.generate(packet_two, "offer-1")

            self.assertEqual(calls, ["ru", "de"])
            self.assertFalse(first.from_cache)
            self.assertFalse(second.from_cache)
            self.assertEqual(first.data["language"], ["ru"])
            self.assertEqual(second.data["language"], ["de"])

    def test_invalid_output_retry_then_fail(self) -> None:
        calls: list[str] = []

        def broken_client(packet, validation_errors=None):
            calls.append("call")
            if validation_errors:
                return {"format": "inpage_push"}
            return {"format": "classic_push"}  # missing required fields

        service = StrategyService(cache=StrategyCache(path=Path(tempfile.gettempdir()) / "tmp_cache.json"), ai_client=broken_client)
        packet = load_fixture("de_dyson.json")
        result = service.generate(packet, "999", regenerate=True)
        self.assertIsNone(result.data)
        self.assertIn("invalid ai output", result.error)
        self.assertGreaterEqual(len(calls), 2)
        self.assertTrue(result.debug)


if __name__ == "__main__":
    unittest.main()
