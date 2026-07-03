from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.evidence.base import TRUSTED_SOURCES, EvidenceSource, RawDoc
from app.evidence.clinicaltrials import ClinicalTrialsSource
from app.evidence.crossref import CrossrefSource
from app.evidence.europepmc import EuropePMCSource
from app.evidence.offline_fixtures import OfflineSource
from app.evidence.openfda import OpenFDASource
from app.evidence.pubmed import PubMedSource

log = logging.getLogger("evidence.registry")


def _live_sources() -> list[EvidenceSource]:
    return [
        PubMedSource(),
        EuropePMCSource(),
        CrossrefSource(),
        ClinicalTrialsSource(),
        OpenFDASource(),
    ]


async def _run_source(
    src: EvidenceSource, a: str, b: str, topic: str, limit: int
) -> list[RawDoc]:
    try:
        return await src.search(a, b, topic, limit)
    except Exception as exc:  # noqa: BLE001 - isolate a failing source
        log.warning("source %s failed: %s", src.name, exc)
        return []


def _dedupe(docs: list[RawDoc]) -> list[RawDoc]:
    seen: dict[str, RawDoc] = {}
    for d in docs:
        if d.source not in TRUSTED_SOURCES:
            continue  # allowlist enforcement
        key = d.dedup_key()
        if key not in seen:
            seen[key] = d
    return list(seen.values())


async def retrieve_evidence(
    molecule_a: str,
    molecule_b: str,
    topic: str,
    sources: list[EvidenceSource] | None = None,
) -> list[RawDoc]:
    """Retrieve, allowlist-filter, and dedupe candidate evidence.

    Mode:
      - offline: local fixtures only.
      - live: real trusted-source APIs.
      - auto: try live; if it yields nothing (no network), fall back to offline.
    Tests inject `sources` directly for determinism.
    """
    settings = get_settings()
    limit = settings.max_docs_per_source

    if sources is not None:
        srcs = sources
    elif settings.evidence_mode == "offline":
        srcs = [OfflineSource()]
    else:
        srcs = _live_sources()

    results = await asyncio.gather(
        *(_run_source(s, molecule_a, molecule_b, topic, limit) for s in srcs)
    )
    docs = _dedupe([d for group in results for d in group])

    if not docs and settings.evidence_mode == "auto" and sources is None:
        log.info("live retrieval empty; falling back to offline fixtures")
        fallback = await OfflineSource().search(molecule_a, molecule_b, topic, limit)
        docs = _dedupe(fallback)

    return docs
