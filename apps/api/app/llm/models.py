from __future__ import annotations

# USD per 1M tokens (input, output) — from the current Claude model catalog.
MODEL_PRICE: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = MODEL_PRICE.get(model, (0.0, 0.0))
    return round(input_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout, 4)
