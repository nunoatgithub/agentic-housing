"""Standalone adapter for DeepSeek's Anthropic-compatible API, with thinking disabled.

    ask_deepseek(prompt) -> Reply

The experiment's Claude Code calls carry a system wrapper and an environment message. This adapter sends only the
system line and the prompt, sets thinking: {"type": "disabled"}, and records agent_cli "deepseek-api".
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from .run_agents import Reply

DEFAULT_BASE_URL = "https://api.deepseek.com/anthropic"
DEFAULT_MODEL = "deepseek-flash"
MAX_OUTPUT_TOKENS = 128000
SYSTEM_PROMPT = "You are a helpful assistant."
ADAPTER_VERSION = "1"
TIMEOUT_SECONDS = 1800

# DeepSeek's published prices, USD per million tokens; peak is 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday.
PRICES = {"off": {"hit": 0.003, "miss": 0.15, "out": 0.60},
          "peak": {"hit": 0.006, "miss": 0.30, "out": 1.20}}


def is_peak(at: datetime) -> bool:
    return at.weekday() < 5 and (1 <= at.hour < 4 or 6 <= at.hour < 10)


def cost_usd(input_tokens: int, cache_read: int, output_tokens: int, at: Optional[datetime] = None) -> float:
    """The DeepSeek price of one call, from the token counts and the published off-peak/peak table."""
    at = at or datetime.now(timezone.utc)
    price = PRICES["peak" if is_peak(at) else "off"]
    return round((input_tokens * price["miss"] + cache_read * price["hit"] + output_tokens * price["out"]) / 1_000_000, 6)


def _api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("no DeepSeek API key: set DEEPSEEK_API_KEY")
    return key


def _base_url() -> str:
    return (os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def ask_deepseek(prompt: str, model_id: str = DEFAULT_MODEL, effort: Optional[str] = None) -> Reply:
    """One request to /v1/messages; thinking is disabled unless an effort level is given."""
    body = {
        "model": model_id,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "disabled"} if effort is None else {"type": "enabled"},
    }
    if effort is not None:
        body["output_config"] = {"effort": effort}
    request = urllib.request.Request(
        _base_url() + "/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01",
                 "Authorization": "Bearer " + _api_key()},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError("DeepSeek API failed: HTTP %s: %s" % (exc.code, detail)) from exc
    duration_ms = round((time.monotonic() - started) * 1000)
    data = json.loads(raw)
    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    usage = data.get("usage") or {}
    input_tokens = usage.get("input_tokens") or 0
    cache_write = usage.get("cache_creation_input_tokens") or 0
    cache_read = usage.get("cache_read_input_tokens") or 0
    output_tokens = usage.get("output_tokens") or 0
    stop_reason = data.get("stop_reason")
    return Reply(
        "" if stop_reason == "max_tokens" else text,
        {
            "input_tokens": input_tokens + cache_write,
            "cache_creation_input_tokens": cache_write,
            "cache_read_input_tokens": cache_read,
            "output_tokens": output_tokens,
            "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens", 0),
            "cost_usd": cost_usd(input_tokens + cache_write, cache_read, output_tokens),
            "duration_ms": duration_ms,
        },
        cut_off=stop_reason == "max_tokens",
        metadata={"deepseek_stop_reason": stop_reason, "deepseek_model": data.get("model"),
                  "deepseek_effort": effort},
    )
