from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.evidence.base import EvidenceSource, RawDoc

log = logging.getLogger("evidence.openfda")

_URL = "https://api.fda.gov/drug/label.json"


class OpenFDASource(EvidenceSource):
    name = "fda"

    async def _label(self, client: httpx.AsyncClient, molecule: str) -> RawDoc | None:
        try:
            r = await client.get(
                _URL,
                params={"search": f'openfda.generic_name:"{molecule}"', "limit": 1},
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            results = r.json().get("results", [])
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("openFDA lookup failed for %s: %s", molecule, exc)
            return None
        if not results:
            return None
        label = results[0]
        openfda = label.get("openfda", {})
        set_id = label.get("set_id") or (openfda.get("spl_set_id") or [None])[0]
        return RawDoc(
            source="fda",
            title=f"FDA drug label: {molecule}",
            external_id=set_id,
            abstract=" ".join(
                label.get("warnings", []) or label.get("indications_and_usage", []) or []
            )[:2000],
            study_design="drug_label",
            url=(
                f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}"
                if set_id
                else None
            ),
            metadata={"brand": openfda.get("brand_name")},
        )

    async def search(
        self, molecule_a: str, molecule_b: str, topic: str, limit: int
    ) -> list[RawDoc]:
        docs: list[RawDoc] = []
        async with httpx.AsyncClient(timeout=get_settings().http_timeout) as client:
            for mol in (molecule_a, molecule_b):
                doc = await self._label(client, mol)
                if doc:
                    docs.append(doc)
        return docs
