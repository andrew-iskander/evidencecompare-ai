from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.molecule import MoleculeOut, MoleculeSearchOut

router = APIRouter(prefix="/molecules", tags=["molecules"])

# Phase 2 seed list. Phase 3 replaces this with RxNorm/ATC normalization.
_SEED: list[MoleculeOut] = [
    MoleculeOut(name="Telmisartan", atc_code="C09CA07", synonyms=["Micardis"]),
    MoleculeOut(name="Valsartan", atc_code="C09CA03", synonyms=["Diovan"]),
    MoleculeOut(name="Losartan", atc_code="C09CA01", synonyms=["Cozaar"]),
    MoleculeOut(name="Empagliflozin", atc_code="A10BK03", synonyms=["Jardiance"]),
    MoleculeOut(name="Dapagliflozin", atc_code="A10BK01", synonyms=["Farxiga"]),
    MoleculeOut(name="Atorvastatin", atc_code="C10AA05", synonyms=["Lipitor"]),
    MoleculeOut(name="Rosuvastatin", atc_code="C10AA07", synonyms=["Crestor"]),
    MoleculeOut(name="Ramipril", atc_code="C09AA05", synonyms=["Altace"]),
    MoleculeOut(name="Metoprolol", atc_code="C07AB02", synonyms=["Lopressor"]),
    MoleculeOut(name="Metformin", atc_code="A10BA02", synonyms=["Glucophage"]),
]


@router.get("/search", response_model=MoleculeSearchOut)
async def search_molecules(
    q: str = Query(default="", max_length=100),
) -> MoleculeSearchOut:
    ql = q.strip().lower()
    if not ql:
        return MoleculeSearchOut(results=_SEED[:8])
    matches = [
        m
        for m in _SEED
        if ql in m.name.lower() or any(ql in s.lower() for s in m.synonyms)
    ]
    return MoleculeSearchOut(results=matches[:10])
