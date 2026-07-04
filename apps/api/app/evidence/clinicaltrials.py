from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import EvidenceSource, RawDoc

log = logging.getLogger("evidence.clinicaltrials")

_URL = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsSource(EvidenceSource):
    name = "clinicaltrials"

    async def search(
        self,
        molecule_a: str,
        molecule_b: str,
        topic: str,
        limit: int,
        query: str | None = None,
    ) -> list[RawDoc]:
        term = query or f"({molecule_a} OR {molecule_b}) {topic}"
        try:
            async with httpx.AsyncClient(timeout=get_settings().http_timeout) as client:
                r = await client.get(
                    _URL,
                    params={"query.term": term, "pageSize": min(limit, 50), "format": "json"},
                )
                r.raise_for_status()
                studies = r.json().get("studies", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("ClinicalTrials.gov search failed: %s", exc)
            return []

        docs: list[RawDoc] = []
        for study in studies[:limit]:
            proto = study.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            nct = ident.get("nctId")
            title = ident.get("briefTitle")
            if not title or not nct:
                continue
            design = proto.get("designModule", {})
            enroll = design.get("enrollmentInfo", {}).get("count")
            start = proto.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
            year = int(start[:4]) if start[:4].isdigit() else None
            docs.append(
                RawDoc(
                    source="clinicaltrials",
                    title=title,
                    external_id=nct,
                    study_design="trial_registry",
                    publication_year=year,
                    sample_size=int(enroll) if enroll else None,
                    url=f"https://clinicaltrials.gov/study/{nct}",
                    metadata={"phase": design.get("phases")},
                )
            )
        return docs
