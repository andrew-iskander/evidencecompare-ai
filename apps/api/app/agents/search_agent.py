"""Search Agent — turns a clinical question into optimized queries, then retrieves.

Live: Claude proposes several optimized boolean/keyword queries for the trusted
sources. Offline: deterministic query variants. Either way, retrieval itself goes
through the trusted-source registry (allowlist + dedupe enforced there).
"""

from __future__ import annotations

import logging

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.core.config import get_settings
from app.evidence.registry import retrieve_evidence
from app.llm.client import llm_live_enabled, structured_call

log = logging.getLogger("agents.search")

_QUERY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "queries": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 6,
        }
    },
    "required": ["queries"],
}

_SYSTEM = (
    "You are a medical librarian. Given two molecules and a clinical topic, produce "
    "3-5 precise literature-search queries (boolean/keyword) suitable for PubMed and "
    "Europe PMC. Prefer queries that surface randomized trials, meta-analyses, and "
    "guidelines comparing the two molecules for the topic. Return queries only."
)


def _offline_queries(a: str, b: str, topic: str) -> list[str]:
    return [
        f'("{a}" OR "{b}") AND "{topic}"',
        f'"{a}" AND "{topic}"',
        f'"{b}" AND "{topic}"',
        f'("{a}" AND "{b}") AND ("{topic}" OR outcomes)',
    ]


class SearchAgent(Agent):
    key = "search"
    label = "Search Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        model_used: str | None = None
        in_tok = out_tok = 0
        cost = 0.0
        primary_query: str | None = None

        if llm_live_enabled():
            try:
                res = await structured_call(
                    model=get_settings().model_agent,
                    system=_SYSTEM,
                    user=f"Molecule A: {a}\nMolecule B: {b}\nClinical topic: {t}",
                    schema=_QUERY_SCHEMA,
                    max_tokens=1024,
                )
                queries = [q for q in res.data.get("queries", []) if q.strip()]
                if queries:
                    state.queries = queries
                    primary_query = queries[0]
                    model_used, in_tok, out_tok, cost = (
                        res.model, res.input_tokens, res.output_tokens, res.cost_usd
                    )
            except Exception as exc:  # noqa: BLE001
                log.warning("live query generation failed, using offline queries: %s", exc)

        if not state.queries:
            state.queries = _offline_queries(a, b, t)

        docs = await retrieve_evidence(a, b, t, sources=state.sources, query=primary_query)
        state.raw_docs = docs
        state.snapshot["queries"] = state.queries
        state.snapshot["candidates"] = len(docs)

        return AgentOutcome(
            detail=f"{len(state.queries)} queries -> {len(docs)} candidate(s)",
            model=model_used,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )
