from typing import Any, Dict, List

import requests

FEED_URL = "https://www.cpagrip.com/common/offer_feed_json.php"


class CPAGripClient:
    def __init__(self, base_url: str = FEED_URL) -> None:
        self.base_url = base_url

    def build_params(self, **kwargs: Any) -> Dict[str, Any]:
        return {k: v for k, v in kwargs.items() if v not in (None, "")}

    def fetch_offers(self, **params: Any) -> Dict[str, Any]:
        query_params = self.build_params(**params)
        try:
            response = requests.get(self.base_url, params=query_params, timeout=10)
            if response.status_code == 403:
                raise PermissionError("Access forbidden: check your private key")
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.JSONDecodeError as exc:  # type: ignore[attr-defined]
            raise ValueError("Invalid JSON received") from exc
        except requests.Timeout as exc:
            raise TimeoutError("Request timed out") from exc
        except requests.RequestException as exc:  # noqa: BLE001
            raise ConnectionError(str(exc)) from exc

        if not isinstance(data, dict) or "offers" not in data:
            raise ValueError("Invalid response: 'offers' key missing")

        offers = data.get("offers", [])
        if not offers:
            raise ValueError("No offers returned by feed")
        return data

    def fetch_offers_list(self, **params: Any) -> List[Dict[str, Any]]:
        payload = self.fetch_offers(**params)
        return payload.get("offers", [])
