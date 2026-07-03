from __future__ import annotations

from pydantic import BaseModel


class MoleculeOut(BaseModel):
    name: str
    atc_code: str | None = None
    rxnorm_id: str | None = None
    synonyms: list[str] = []


class MoleculeSearchOut(BaseModel):
    results: list[MoleculeOut]
