from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import EvidenceSource, RawDoc

log = logging.getLogger("evidence.crossref")

_URL = "https://api.crossref.org/works"


class CrossrefSource(EvidenceSource):
    name = "crossref"

    async def search(
        self, molecule_a: str, molecule_b: str, topic: str, limit: int
    ) -> list[RawDoc]:
        query = f"{molecule_a} {molecule_b} {topic}"
        s = get_settings()
        headers = {"User-Agent": f"EvidenceCompare/0.1 (mailto:{s.ncbi_email})"}
        try:
            async with httpx.AsyncClient(timeout=s.http_timeout, headers=headers) as client:
                r = await client.get(
                    _URL,
                    params={
                        "query.bibliographic": query,
                        "rows": limit,
                        "select": "DOI,title,issued,container-title,type",
                    },
                )
                r.raise_for_status()
                items = r.json().get("message", {}).get("items", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("Crossref search failed: %s", exc)
            return []

        docs: list[RawDoc] = []
        for item in items:
            titles = item.get("title") or []
            if not titles:
                continue
            year = None
            issued = item.get("issued", {}).get("date-parts", [[None]])
            if issued and issued[0] and issued[0][0]:
                year = issued[0][0]
            docs.append(
                RawDoc(
                    source="crossref",
                    title=titles[0],
                    doi=item.get("DOI"),
                    study_design="other",
                    publication_year=int(year) if year else None,
                    url=f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else None,
                    metadata={"type": item.get("type")},
                )
            )
        return docs
