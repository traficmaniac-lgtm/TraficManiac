from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_FILE = Path(__file__).resolve().parent / "strategy_cache.json"


class StrategyCache:
    def __init__(self, path: Path = CACHE_FILE):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)

    def build_key(
        self,
        offer_id: str,
        traffic_source: str,
        budget: float,
        payload_fingerprint: str,
        app_version: str = "0.2",
        schema_version: str = "v1",
    ) -> str:
        return f"{offer_id}|{traffic_source}|{budget}|payload_{payload_fingerprint}|v{app_version}|schema_{schema_version}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._read().get(key)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        data = self._read()
        data[key] = value
        self._write(data)


__all__ = ["StrategyCache"]
