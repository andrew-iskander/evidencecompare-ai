"""Citation-Verification Agent — the anti-hallucination gate.

Verifies every selected citation against its source (DOI/PMID/registry resolves;
offline, a trusted-source record is treated as resolved). Only resolvable studies
survive into `state.verified`, which is re-keyed contiguously (c1..cN). Because
upstream agents (Trial-Extraction, Guideline, Safety, Evidence-Ranking, Conflict)
already stamped the provisional ref_keys, this agent remaps their outputs to the
final keys and drops any reference whose source failed verification — so no report
artifact can point at an unverified or invented citation.

Offline the remap is the identity (all trusted records resolve), so deterministic
tests see stable c1..cN keys.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.rag.ranking import RankedDoc
from app.rag.verifier import verify_doc


def _remap_ids(ids: list[str], remap: dict[str, str]) -> list[str]:
    return [remap[i] for i in ids if i in remap]


class CitationVerificationAgent(Agent):
    key = "verification"
    label = "Citation-Verification Agent"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        ranked = state.ranked
        verified: list[RankedDoc] = []
        broken: list[dict] = []
        for rd in ranked:
            if await verify_doc(rd.doc):
                verified.append(rd)
            else:
                broken.append({"ref_key": rd.ref_key, "title": rd.doc.title,
                               "doi": rd.doc.doi, "pmid": rd.doc.pmid})

        # Contiguous re-key: build old->new from current keys, then apply.
        remap = {rd.ref_key: f"c{i + 1}" for i, rd in enumerate(verified)}
        for i, rd in enumerate(verified):
            rd.ref_key = f"c{i + 1}"
        state.verified = verified

        # Remap every upstream artifact that referenced provisional keys.
        keep = set(remap)
        state.extractions = [
            {**ex, "ref_key": remap[ex["ref_key"]]}
            for ex in state.extractions
            if ex.get("ref_key") in keep
        ]
        if state.guideline_summary:
            for claim in state.guideline_summary.get("claims", []):
                claim["citation_ids"] = _remap_ids(claim.get("citation_ids", []), remap)
        if state.safety_matrix:
            for row in state.safety_matrix.get("rows", []):
                for side in ("a", "b"):
                    cell = row.get(side, {})
                    cell["citation_ids"] = _remap_ids(cell.get("citation_ids", []), remap)
        if state.scores.get("studies"):
            state.scores["studies"] = [
                {**s, "ref_key": remap[s["ref_key"]]}
                for s in state.scores["studies"]
                if s.get("ref_key") in keep
            ]
        if state.reconciliation:
            for exp in state.reconciliation.get("explanations", []):
                exp["favors_refs"] = _remap_ids(exp.get("favors_refs", []), remap)
                exp["against_refs"] = _remap_ids(exp.get("against_refs", []), remap)

        state.verification = {
            "checked": len(ranked),
            "verified": len(verified),
            "removed": len(broken),
            "broken": broken[:8],
        }
        state.snapshot["verified"] = len(verified)
        return AgentOutcome(
            detail=(
                f"verified {len(verified)}/{len(ranked)} citation(s)"
                + (f", removed {len(broken)} unresolved" if broken else "")
            )
        )
