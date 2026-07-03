from __future__ import annotations

import hashlib
import logging
import math
import re

import httpx

from app.core.config import get_settings

log = logging.getLogger("rag.embeddings")

_TOKEN = re.compile(r"[a-z0-9]+")
_VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _offline_embed(text: str, dim: int) -> list[float]:
    """Deterministic hashed bag-of-words embedding.

    Not a semantic model, but shared vocabulary yields higher cosine similarity —
    enough to drive relevance ranking offline and in tests. Live mode uses Voyage.
    """
    vec = [0.0] * dim
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


async def _voyage_embed(texts: list[str], api_key: str) -> list[list[float]] | None:
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=s.http_timeout) as client:
            r = await client.post(
                _VOYAGE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"input": texts, "model": s.embedding_model},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            return [d["embedding"] for d in data]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        log.warning("Voyage embeddings failed, falling back to offline: %s", exc)
        return None


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    s = get_settings()
    use_live = s.llm_mode != "offline" and bool(s.voyage_api_key)
    if use_live:
        result = await _voyage_embed(texts, s.voyage_api_key)
        if result is not None:
            return result
    dim = s.embedding_dim
    return [_offline_embed(t, dim) for t in texts]


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
