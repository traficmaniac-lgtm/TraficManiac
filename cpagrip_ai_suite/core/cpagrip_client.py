from __future__ import annotations

from typing import Any, Dict, List

import requests

from .offer_model import OfferRaw, parse_offer

FEED_URL = "https://www.cpagrip.com/common/offer_feed_json.php"


class CPAGripClient:
    def __init__(self, base_url: str = FEED_URL) -> None:
        self.base_url = base_url

    def build_params(self, **kwargs: Any) -> Dict[str, Any]:
        return {k: v for k, v in kwargs.items() if v not in (None, "")}

    def fetch_offers(self, **params: Any) -> Dict[str, Any]:
        query_params = self.build_params(**params)
        try:
            response = requests.get(self.base_url, params=query_params, timeout=15)
            if response.status_code == 403:
                raise PermissionError("Доступ запрещен: проверь приватный ключ")
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.JSONDecodeError as exc:  # type: ignore[attr-defined]
            raise ValueError("Неверный JSON в ответе") from exc
        except requests.Timeout as exc:
            raise TimeoutError("Таймаут запроса к фиду") from exc
        except requests.RequestException as exc:  # noqa: BLE001
            raise ConnectionError(str(exc)) from exc

        if not isinstance(data, dict) or "offers" not in data:
            raise ValueError("Неправильный ответ: нет ключа 'offers'")

        offers = data.get("offers", [])
        if not offers:
            raise ValueError("Фид вернул 0 офферов")
        return data

    def fetch_offers_list(self, **params: Any) -> List[Dict[str, Any]]:
        payload = self.fetch_offers(**params)
        return payload.get("offers", [])

    def fetch_raw_offers(self, **params: Any) -> List[OfferRaw]:
        offers = self.fetch_offers_list(**params)
        return [parse_offer(item) for item in offers]
