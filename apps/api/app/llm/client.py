"""Shared Claude client helper for the specialist agents.

Centralizes the one way we call Claude for structured output so every agent
(Search, Guideline, Trial-Extraction, Comparison, Medical-Writer) uses the same
current-API conventions (adaptive thinking, high effort, JSON-schema structured
outputs, prompt-cached system prompt) and the same cost accounting. Live-only;
callers decide when to use it and always keep a deterministic offline fallback.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.llm.models import cost_usd

log = logging.getLogger("llm.client")


@dataclass
class LLMResult:
    data: dict
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


def llm_live_enabled() -> bool:
    """True when live LLM calls are permitted (mode on + key present)."""
    s = get_settings()
    return s.llm_mode != "offline" and bool(s.anthropic_api_key)


async def structured_call(
    *,
    model: str,
    system: str,
    user: str,
    schema: dict,
    max_tokens: int = 8000,
) -> LLMResult:
    """Call Claude for a JSON object matching `schema`. Raises on failure.

    Uses current-model conventions only (no temperature/top_p/budget_tokens,
    no prefills). Callers must wrap this in try/except and fall back to a
    deterministic path so the app stays fully functional offline.
    """
    import anthropic  # lazy: offline/tests never import the SDK

    client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": schema},
        },
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()

    text = next(
        (b.text for b in message.content if getattr(b, "type", None) == "text"), "{}"
    )
    data = json.loads(text)
    usage = message.usage
    return LLMResult(
        data=data,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost_usd=cost_usd(model, usage.input_tokens, usage.output_tokens),
    )
