from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import EvidenceSource, RawDoc

log = logging.getLogger("evidence.pubmed")

_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

_DESIGN_HINTS = {
    "meta-analysis": "meta_analysis",
    "systematic review": "systematic_review",
    "randomized": "rct",
    "randomised": "rct",
    "guideline": "guideline",
    "practice guideline": "guideline",
}


def _classify(title: str, pubtypes: list[str]) -> str:
    hay = (title + " " + " ".join(pubtypes)).lower()
    for needle, design in _DESIGN_HINTS.items():
        if needle in hay:
            return design
    return "other"


class PubMedSource(EvidenceSource):
    name = "pubmed"

    def _params(self, extra: dict) -> dict:
        s = get_settings()
        base = {"retmode": "json", "tool": "evidencecompare", "email": s.ncbi_email}
        if s.ncbi_api_key:
            base["api_key"] = s.ncbi_api_key
        return {**base, **extra}

    async def search(
        self,
        molecule_a: str,
        molecule_b: str,
        topic: str,
        limit: int,
        query: str | None = None,
    ) -> list[RawDoc]:
        term = query or f'("{molecule_a}" OR "{molecule_b}") AND "{topic}"'
        timeout = get_settings().http_timeout
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(
                    f"{_EUTILS}/esearch.fcgi",
                    params=self._params({"db": "pubmed", "term": term, "retmax": limit}),
                )
                r.raise_for_status()
                ids = r.json().get("esearchresult", {}).get("idlist", [])
                if not ids:
                    return []

                r2 = await client.get(
                    f"{_EUTILS}/esummary.fcgi",
                    params=self._params({"db": "pubmed", "id": ",".join(ids)}),
                )
                r2.raise_for_status()
                result = r2.json().get("result", {})
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("PubMed search failed: %s", exc)
            return []

        docs: list[RawDoc] = []
        for uid in result.get("uids", []):
            item = result.get(uid, {})
            title = item.get("title", "").rstrip(".")
            if not title:
                continue
            doi = None
            for aid in item.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
            year = None
            pubdate = item.get("pubdate", "")
            if pubdate[:4].isdigit():
                year = int(pubdate[:4])
            docs.append(
                RawDoc(
                    source="pubmed",
                    title=title,
                    pmid=uid,
                    doi=doi,
                    study_design=_classify(title, item.get("pubtype", [])),
                    publication_year=year,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    metadata={"journal": item.get("fulljournalname")},
                )
            )
        return docs
