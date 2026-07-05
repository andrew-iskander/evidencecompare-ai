"""Conflict-Resolution Agent — detects conflicting evidence and reconciles it.

Builds on the deterministic conflict detector (`pipeline.quality.detect_conflicts`,
which flags molecules whose studies report opposite *significant* primary effect
directions) and adds an explanation of *why* the studies disagree — differences in
population, comparator, sample size, study design, and reported precision — drawn
only from the structured extractions. It never invents a conflict the numbers don't
show, and never resolves a genuine disagreement by fiat: it surfaces the axes of
heterogeneity so a clinician can judge.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.pipeline.quality import _direction, detect_conflicts


def _studies_for(molecule: str, extractions: list[dict]) -> list[dict]:
    low = molecule.lower()
    out = []
    for ex in extractions:
        hay = f"{ex.get('intervention') or ''} {ex.get('title') or ''}".lower()
        if low in hay:
            out.append(ex)
    return out


def _explain(molecule: str, extractions: list[dict]) -> dict:
    studies = _studies_for(molecule, extractions)
    favors, against = [], []
    for ex in studies:
        d = _direction(ex)
        if not (d and d[1]):
            continue
        if d[0] == "favors":
            favors.append(ex)
        elif d[0] == "against":
            against.append(ex)

    axes: list[str] = []
    comps = {ex.get("comparator") for ex in studies if ex.get("comparator")}
    if len(comps) > 1:
        axes.append(f"different comparators ({', '.join(sorted(str(c) for c in comps))})")
    pops = {ex.get("population") for ex in studies if ex.get("population")}
    if len(pops) > 1:
        axes.append("different study populations")
    sizes = [n for ex in studies if isinstance((n := ex.get("sample_size")), int)]
    if sizes and (max(sizes) >= 4 * max(1, min(sizes))):
        axes.append(f"large differences in sample size ({min(sizes)}–{max(sizes)})")
    designs = {ex.get("study_design") for ex in studies if ex.get("study_design")}
    if len(designs) > 1:
        axes.append(f"mixed study designs ({', '.join(sorted(str(d) for d in designs))})")

    return {
        "molecule": molecule,
        "favors_refs": [ex["ref_key"] for ex in favors],
        "against_refs": [ex["ref_key"] for ex in against],
        "axes": axes,
        "text": (
            f"For {molecule}, retrieved studies point in opposite directions on their "
            f"primary effect. Likely drivers of the disagreement: "
            + (", ".join(axes) if axes else "methodological/precision differences not "
               "fully characterized in the abstracts")
            + ". Interpret pooled conclusions with caution."
        ),
    }


class ConflictResolutionAgent(Agent):
    key = "conflict"
    label = "Conflict-Resolution Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b = state.molecule_a, state.molecule_b
        notes = detect_conflicts(state.extractions, a, b)
        state.conflicts = notes

        explanations = []
        for mol in (a, b):
            if any(mol.lower() in n.lower() for n in notes):
                explanations.append(_explain(mol, state.extractions))

        consistency = state.scores.get("overall", {}).get("consistency_score")
        state.reconciliation = {
            "has_conflict": bool(notes),
            "notes": notes,
            "explanations": explanations,
            "consistency_score": consistency,
            "summary": (
                "Retrieved evidence is internally consistent on primary effect direction."
                if not notes
                else f"{len(notes)} conflict(s) detected across the evidence base; "
                "see reconciliation for the axes of heterogeneity."
            ),
        }
        return AgentOutcome(
            detail=(
                "no conflicts detected" if not notes
                else f"{len(notes)} conflict(s) reconciled"
            )
        )
