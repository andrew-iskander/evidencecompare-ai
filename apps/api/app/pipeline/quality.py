"""Quality control: transparency-layer assignment + conflicting-evidence detection.

Transparency layers keep the report honest by separating what was *found* from
what the AI *concluded* from what a clinician should *take away*:
  - retrieved_evidence : raw facts (extractions, citations, comparison table)
  - ai_interpretation  : synthesized narrative over the retrieved evidence
  - clinical_summary   : concise takeaways (executive summary + clinical pearls)

Conflict detection is deterministic over the structured extractions: it flags
when studies for the same molecule report opposite, statistically significant
effect directions. It never invents a conflict that the numbers don't show.
"""

from __future__ import annotations

import re

# Sections that belong to the clinical-summary layer; everything else is
# AI interpretation. (Retrieved evidence is rendered from structured data, not
# from narrative sections.)
_CLINICAL_SUMMARY = {"executive_summary", "clinical_pearls"}


def layer_for(section_key: str) -> str:
    return "clinical_summary" if section_key in _CLINICAL_SUMMARY else "ai_interpretation"


_NUM = re.compile(r"(\d+(?:\.\d+)?)")


def _effect_value(text: str | None) -> float | None:
    if not text:
        return None
    m = _NUM.search(text)
    return float(m.group(1)) if m else None


def _ci_bounds(text: str | None) -> tuple[float, float] | None:
    if not text:
        return None
    nums = _NUM.findall(text)
    if len(nums) >= 2:
        lo, hi = float(nums[-2]), float(nums[-1])
        return (min(lo, hi), max(lo, hi))
    return None


def _direction(extraction: dict) -> tuple[str, bool] | None:
    """(direction, significant) for a study's primary effect, or None if absent.

    direction: 'favors' (point estimate < 1), 'against' (> 1), 'neutral' (~1).
    significant: False when the 95% CI crosses 1 (or a reported p >= 0.05).
    """
    text = extraction.get("hazard_ratio") or extraction.get("relative_risk")
    value = _effect_value(text)
    if value is None:
        return None

    significant = True
    ci = _ci_bounds(extraction.get("confidence_interval"))
    if ci and ci[0] <= 1.0 <= ci[1]:
        significant = False
    p = _effect_value(extraction.get("p_value"))
    if p is not None and p >= 0.05:
        significant = False

    if abs(value - 1.0) < 1e-9:
        return ("neutral", significant)
    return ("favors" if value < 1.0 else "against", significant)


def detect_conflicts(extractions: list[dict], molecule_a: str, molecule_b: str) -> list[str]:
    """Flag molecules whose studies report opposite significant effect directions."""
    notes: list[str] = []
    for mol in (molecule_a, molecule_b):
        low = mol.lower()
        dirs: set[str] = set()
        for ex in extractions:
            hay = f"{ex.get('intervention') or ''} {ex.get('title') or ''}".lower()
            if low not in hay:
                continue
            d = _direction(ex)
            if d and d[1] and d[0] in ("favors", "against"):
                dirs.add(d[0])
        if "favors" in dirs and "against" in dirs:
            notes.append(
                f"Conflicting evidence for {mol}: retrieved studies report both a "
                f"significant benefit and a significant harm/adverse direction on their "
                f"primary effect estimate. Interpret with caution."
            )
    return notes
