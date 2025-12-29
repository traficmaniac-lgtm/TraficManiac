from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator

from .openai_client import generate_propeller_settings
from .propeller_schema import PROP_SCHEMA
from ..cache.strategy_cache import StrategyCache


class StrategyResult:
    def __init__(self, data: Dict[str, Any] | None = None, debug: str = "", error: str | None = None, from_cache: bool = False):
        self.data = data
        self.debug = debug
        self.error = error
        self.from_cache = from_cache


class StrategyService:
    def __init__(self, cache: StrategyCache | None = None, ai_client=generate_propeller_settings):
        self.cache = cache or StrategyCache()
        self.ai_client = ai_client
        self.validator = Draft202012Validator(PROP_SCHEMA)

    @staticmethod
    def _fingerprint_payload(payload: Dict[str, Any]) -> str:
        try:
            serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        except TypeError:
            serialized = repr(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = sorted(self.validator.iter_errors(payload), key=lambda e: e.path)
        if not errors:
            return True, []
        messages = [f"{list(err.path)}: {err.message}" for err in errors]
        return False, messages

    def generate(self, ai_packet: Dict[str, Any], offer_id: str, regenerate: bool = False) -> StrategyResult:
        payload_fingerprint = self._fingerprint_payload(ai_packet)
        cache_key = self.cache.build_key(
            offer_id,
            ai_packet.get("traffic_source", "PropellerAds"),
            ai_packet.get("constraints", {}).get("test_budget_usd", 30),
            payload_fingerprint,
        )
        if not regenerate:
            cached = self.cache.get(cache_key)
            if cached:
                return StrategyResult(data=cached, from_cache=True)

        attempt_debug: List[str] = []
        # first attempt
        try:
            generated = self.ai_client(ai_packet)
        except Exception as exc:  # noqa: BLE001
            return StrategyResult(error=str(exc), debug="\n".join(attempt_debug))

        ok, errors = self.validate(generated)
        if ok:
            self.cache.set(cache_key, generated)
            return StrategyResult(data=generated)

        attempt_debug.append("Initial validation failed: " + "; ".join(errors))

        # retry with validation errors
        try:
            regenerated = self.ai_client(ai_packet, validation_errors=errors)
        except Exception as exc:  # noqa: BLE001
            return StrategyResult(error=str(exc), debug="\n".join(attempt_debug))

        ok, errors = self.validate(regenerated)
        if ok:
            self.cache.set(cache_key, regenerated)
            return StrategyResult(data=regenerated, debug="\n".join(attempt_debug))

        attempt_debug.append("Retry validation failed: " + "; ".join(errors))
        raw = json.dumps(regenerated, ensure_ascii=False, indent=2) if isinstance(regenerated, dict) else str(regenerated)
        return StrategyResult(error="invalid ai output", debug="\n".join(attempt_debug + [raw]))


__all__ = ["StrategyService", "StrategyResult"]
