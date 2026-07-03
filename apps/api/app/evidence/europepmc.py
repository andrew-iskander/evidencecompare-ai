from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import EvidenceSource, RawDoc

log = logging.getLogger("evidence.europepmc")

_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _classify(pub_types: str) -> str:
    t = pub_types.lower()
    if "meta-analysis" in t:
        return "meta_analysis"
    if "systematic review" in t:
        return "systematic_review"
    if "randomized" in t or "randomised" in t:
        return "rct"
    if "guideline" in t:
        return "guideline"
    return "other"


class EuropePMCSource(EvidenceSource):
    name = "europepmc"

    async def search(
        self, molecule_a: str, molecule_b: str, topic: str, limit: int
    ) -> list[RawDoc]:
        query = f'("{molecule_a}" OR "{molecule_b}") AND "{topic}"'
        try:
            async with httpx.AsyncClient(timeout=get_settings().http_timeout) as client:
                r = await client.get(
                    _URL,
                    params={
                        "query": query,
                        "format": "json",
                        "pageSize": limit,
                        "resultType": "core",
                    },
                )
                r.raise_for_status()
                results = r.json().get("resultList", {}).get("result", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("Europe PMC search failed: %s", exc)
            return []

        docs: list[RawDoc] = []
        for item in results:
            title = (item.get("title") or "").rstrip(".")
            if not title:
                continue
            year = item.get("pubYear")
            pub_types = " ".join(
                item.get("pubTypeList", {}).get("pubType", [])
                if isinstance(item.get("pubTypeList"), dict)
                else []
            )
            docs.append(
                RawDoc(
                    source="europepmc",
                    title=title,
                    pmid=item.get("pmid"),
                    doi=item.get("doi"),
                    abstract=item.get("abstractText", "") or "",
                    study_design=_classify(pub_types),
                    publication_year=int(year) if year and str(year).isdigit() else None,
                    url=item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url")
                    if isinstance(item.get("fullTextUrlList"), dict)
                    else None,
                    metadata={"journal": item.get("journalTitle")},
                )
            )
        return docs
