import json
import unittest

from cpagrip_ai_suite.core.offer_classifier import classify_offer
from cpagrip_ai_suite.core.offer_model import normalize_offers
from cpagrip_ai_suite.core.scoring import calculate_profit_score
from cpagrip_ai_suite.core.filters import filter_offers
from cpagrip_ai_suite.prompts.ai_prompts import build_ai_selection_prompt


class OfferSuiteTests(unittest.TestCase):
    def test_classifier_prioritizes_cc_and_collects_risk(self) -> None:
        text = "Credit card submit offer with adult audience"
        result = classify_offer(text)
        self.assertEqual(result.kind, "CC")
        self.assertEqual(result.complexity, 4)
        self.assertAlmostEqual(result.confidence, 0.9)
        self.assertIn("adult", result.risk_flags)

    def test_scoring_applies_penalties(self) -> None:
        score = calculate_profit_score(payout=30, tier="tier1", complexity=4, risk_flags=["adult"], kind="CC")
        self.assertAlmostEqual(score.profit_score, 6.2156)
        self.assertIn("risk penalty", score.explanation)
        self.assertIn("CC/PIN penalty", score.explanation)

    def test_normalization_and_filtering_pipeline(self) -> None:
        raw_offers = [
            {
                "id": "1",
                "title": "Email submit US",
                "payout": 2.5,
                "countries": "US",
                "offerlink": "http://example.com/1",
                "description": "Single opt in email submit",
                "restrictions": "No incent",
                "allowed_traffic": "Social",
                "type": "SOI",
            },
            {
                "id": "2",
                "title": "APK install FR",
                "payout": 1.2,
                "countries": "FR",
                "offerlink": "http://example.com/2",
                "description": "Android install",
                "allowed_countries": "FR",
                "traffic_source": "Push",
                "type": "INSTALL",
            },
        ]
        normalization = normalize_offers(raw_offers)
        self.assertEqual(len(normalization.errors), 0)
        self.assertEqual(len(normalization.offers), 2)
        # SOI should classify to kind SOI and tier1 geo weight
        soi_offer = normalization.offers[0]
        self.assertEqual(soi_offer.kind, "SOI")
        self.assertEqual(soi_offer.geo_tier, "tier1")
        # Filtering by GEO include and kind should keep only matching offer
        filtered = filter_offers(normalization.offers, include_geo=["US"], kind="SOI")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].offer_id, "1")

    def test_ai_prompt_json_roundtrip(self) -> None:
        raw_offers = [
            {
                "id": "10",
                "title": "Quiz CA",
                "payout": 4.0,
                "countries": "CA",
                "offerlink": "http://example.com/quiz",
                "description": "Survey quiz",
                "type": "SURVEY",
            }
        ]
        normalized = normalize_offers(raw_offers).offers
        prompt = build_ai_selection_prompt(normalized, budget=100)
        # Ensure prompt payload after prefix is valid JSON
        payload_str = prompt.split("\n", 1)[1]
        parsed = json.loads(payload_str)
        self.assertIn("offers", parsed)
        self.assertEqual(parsed["budget"], 100)
        self.assertEqual(parsed["offers"][0]["kind"], "SURVEY")


if __name__ == "__main__":
    unittest.main()
