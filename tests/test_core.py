import json
import unittest

from cpagrip_ai_suite.core.offer_model import normalize_offers
from cpagrip_ai_suite.core.scoring import score_offer
from cpagrip_ai_suite.prompts.strategy_packet import build_strategy_packet


class OfferSuiteTests(unittest.TestCase):
    def test_scoring_weights_geo_and_flow(self) -> None:
        offer_score = score_offer(
            payout_usd=10,
            conversion_type="SOI Email Submit",
            geo_allowed=["US", "CA"],
            epc=1.2,
            cr=0.8,
            incentive_allowed=True,
            traffic_forbidden=["brand bidding"],
            cap=50,
        )
        self.assertGreater(offer_score.score, 10)
        self.assertTrue("tier1 bonus" in offer_score.notes)

    def test_normalization_and_strategy_packet(self) -> None:
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

        top_offer = normalization.offers[0]
        strategy_json = build_strategy_packet(top_offer)
        payload = json.loads(strategy_json)
        self.assertEqual(payload["network"], "CPAGrip")
        self.assertIn("offer", payload)
        self.assertIn("tracking", payload)
        self.assertEqual(payload["constraints"]["test_budget_usd"], 30)
        self.assertIn("tracking_url", payload["offer"]["links"])


if __name__ == "__main__":
    unittest.main()
