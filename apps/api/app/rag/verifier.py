from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import RawDoc

log = logging.getLogger("rag.verifier")


async def _resolves(client: httpx.AsyncClient, url: str) -> bool:
    try:
        r = await client.head(url, follow_redirects=True)
        if r.status_code >= 400:
            r = await client.get(url, follow_redirects=True)
        return r.status_code < 400
    except httpx.HTTPError:
        return False


async def verify_doc(doc: RawDoc) -> bool:
    """Verify that a citation resolves to a real record.

    Live mode: resolve the DOI (doi.org) or PubMed/registry URL over HTTP.
    Offline mode: a record returned by a trusted source is treated as resolved
    (the retrieval itself is the source of truth); records with no identifier at
    all cannot be cited.
    """
    settings = get_settings()

    has_identifier = bool(doc.doi or doc.pmid or doc.external_id)
    if not has_identifier:
        return False

    if settings.evidence_mode == "offline" or settings.llm_mode == "offline":
        return True  # trust the (synthetic) trusted-source retrieval

    urls: list[str] = []
    if doc.doi:
        urls.append(f"https://doi.org/{doc.doi}")
    if doc.pmid:
        urls.append(f"https://pubmed.ncbi.nlm.nih.gov/{doc.pmid}/")
    if doc.url:
        urls.append(doc.url)

    if not urls:
        return has_identifier

    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        for url in urls:
            if await _resolves(client, url):
                return True
    return False
