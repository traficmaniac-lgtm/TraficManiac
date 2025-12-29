from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from openai._exceptions import OpenAIError

from .propeller_schema import PROP_SCHEMA
from .strategy_prompt import build_messages
from ...utils.config import load_app_config

REQUEST_TIMEOUT = 45


def _load_api_settings() -> Tuple[str, str, float]:
    config = load_app_config()
    key = os.getenv("OPENAI_API_KEY") or config.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY env or config.json")
    model = str(config.get("OPENAI_MODEL", "gpt-4.1"))
    try:
        temperature = float(config.get("OPENAI_TEMPERATURE", 0.2))
    except (TypeError, ValueError):
        temperature = 0.2
    return str(key), model, temperature


def generate_propeller_settings(ai_packet: Dict[str, Any], validation_errors: Optional[List[str]] = None) -> Dict[str, Any]:
    api_key, model, temperature = _load_api_settings()
    client = OpenAI(api_key=api_key)
    messages = build_messages(ai_packet, validation_errors)
    try:
        completion = client.responses.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "PropellerSettingsSchema", "schema": PROP_SCHEMA, "strict": True},
            },
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
