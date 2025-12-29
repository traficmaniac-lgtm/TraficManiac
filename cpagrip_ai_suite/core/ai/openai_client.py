from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai._exceptions import OpenAIError

from .propeller_schema import PROP_SCHEMA
from .strategy_prompt import build_messages

REQUEST_TIMEOUT = 45


def _load_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    config_path = os.path.join(os.getcwd(), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                key_val = data.get("OPENAI_API_KEY")
                if key_val:
                    return str(key_val)
        except Exception:
            pass
    raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY env or config.json")


def generate_propeller_settings(ai_packet: Dict[str, Any], validation_errors: Optional[List[str]] = None) -> Dict[str, Any]:
    api_key = _load_api_key()
    client = OpenAI(api_key=api_key)
    messages = build_messages(ai_packet, validation_errors)
    try:
        completion = client.responses.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_schema", "json_schema": {"name": "PropellerSettingsSchema", "schema": PROP_SCHEMA, "strict": True}},
            timeout=REQUEST_TIMEOUT,
            store=False,
        )
        # newest sdk: output text? use output[0].content[0].text
        content_blocks = completion.output[0].content if completion.output else []
        payload_text = ""
        for block in content_blocks:
            if hasattr(block, "text"):
                payload_text += block.text
        data = json.loads(payload_text)
        return data
    except OpenAIError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"OpenAI API error: {exc}") from exc
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"OpenAI unexpected error: {exc}") from exc


__all__ = ["generate_propeller_settings"]
