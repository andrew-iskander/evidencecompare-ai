"""Safety Agent — builds a comparative safety matrix for the two molecules.

Deterministic and offline-safe: it scans the retrieved drug labels and studies that
mention each molecule for evidence of each safety domain (contraindications,
warnings, interactions, monitoring, pregnancy, lactation, renal/hepatic dosing,
boxed warnings) and folds in the adverse events already parsed by the Trial-
Extraction agent. Every populated cell carries the ref_key(s) of the source(s) that
mention it; a domain with no supporting text is reported honestly as
"not addressed in retrieved evidence" rather than invented.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.agents.specialists import mentions
from app.rag.ranking import RankedDoc

# (key, label, keyword hints scanned in title+abstract/label text)
_DOMAINS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("contraindications", "Contraindications", ("contraindicat",)),
    ("warnings", "Warnings & Precautions", ("warning", "precaution")),
    ("black_box", "Boxed (Black Box) Warning", ("boxed warning", "black box", "black-box")),
    ("interactions", "Drug Interactions",
     ("interaction", "concomitant", "co-administ", "coadminist")),
    ("monitoring", "Monitoring", ("monitor",)),
    ("pregnancy", "Pregnancy", ("pregnan", "teratogen")),
    ("breastfeeding", "Breastfeeding / Lactation",
     ("lactation", "breastfeed", "breast-feed", "nursing")),
    ("renal", "Renal Dosing", ("renal", "creatinine clearance", "egfr", "kidney")),
    ("hepatic", "Hepatic Dosing", ("hepatic", "liver")),
)


def _cell(docs: list[RankedDoc], hints: tuple[str, ...]) -> dict:
    refs: list[str] = []
    for rd in docs:
        hay = f"{rd.doc.title} {rd.doc.abstract}".lower()
        if any(h in hay for h in hints):
            refs.append(rd.ref_key)
    if refs:
        return {"status": "reported", "citation_ids": refs[:4],
                "note": "Addressed in retrieved evidence."}
    return {"status": "not_reported", "citation_ids": [],
            "note": "Not addressed in retrieved evidence."}


class SafetyAgent(Agent):
    key = "safety"
    label = "Safety Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b = state.molecule_a, state.molecule_b
        a_docs = [rd for rd in state.ranked if mentions(rd, a)]
        b_docs = [rd for rd in state.ranked if mentions(rd, b)]

        rows = []
        populated = 0
        for key, label, hints in _DOMAINS:
            cell_a = _cell(a_docs, hints)
            cell_b = _cell(b_docs, hints)
            if cell_a["status"] == "reported" or cell_b["status"] == "reported":
                populated += 1
            rows.append({"key": key, "label": label, "a": cell_a, "b": cell_b})

        # Adverse events come from the structured extractions (one source of truth).
        ae_a: dict[str, list[str]] = {}
        ae_b: dict[str, list[str]] = {}
        for ex in state.extractions:
            hay = f"{ex.get('intervention') or ''} {ex.get('title') or ''}".lower()
            if a.lower() in hay:
                ae_a.setdefault(ex["ref_key"], ex.get("adverse_events", []))
            if b.lower() in hay:
                ae_b.setdefault(ex["ref_key"], ex.get("adverse_events", []))

        def _ae_cell(byref: dict[str, list[str]]) -> dict:
            terms = sorted({t for v in byref.values() for t in v})
            if terms:
                return {"status": "reported", "citation_ids": list(byref.keys())[:4],
                        "note": ", ".join(terms[:8])}
            return {"status": "not_reported", "citation_ids": [],
                    "note": "No adverse events parsed from retrieved trials."}

        rows.append({
            "key": "adverse_events", "label": "Reported Adverse Events",
            "a": _ae_cell(ae_a), "b": _ae_cell(ae_b),
        })

        state.safety_matrix = {
            "molecule_a": a,
            "molecule_b": b,
            "rows": rows,
        }
        state.snapshot["safety_domains_populated"] = populated
        return AgentOutcome(
            detail=f"safety matrix: {populated}/{len(_DOMAINS)} domains with evidence"
        )
