"""Search Agent — turns the research plan into optimized queries, retrieves, and
produces a ranked, de-duplicated study list.

Per the V3 spec the Search Agent's output is a *ranked study list*, so it owns
retrieval + relevance embedding + evidence-tier ranking + top-k selection, then
assigns each selected study a stable per-report ref_key (c1..cN). Downstream agents
(Guideline, Trial-Extraction, Safety, Evidence-Ranking) read this selected set;
the Citation-Verification agent later prunes any that don't resolve.

Live: Claude proposes optimized boolean/keyword queries seeded by the interpreter's
expanded keywords. Offline: deterministic query variants. Retrieval always flows
through the trusted-source registry (allowlist + dedupe enforced there).
"""

from __future__ import annotations

import logging

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.core.config import get_settings
from app.evidence.registry import retrieve_evidence
from app.llm.client import llm_live_enabled, structured_call
from app.pipeline.comparison import top_tier_label
from app.rag.embeddings import cosine, embed_query, embed_texts
from app.rag.ranking import RankedDoc, rank_docs

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
    "You are a medical librarian. Given two molecules, their synonyms, and a clinical "
    "topic, produce 3-5 precise literature-search queries (boolean/keyword) suitable "
    "for PubMed and Europe PMC. Prefer queries that surface randomized trials, "
    "meta-analyses, and guidelines comparing the two molecules for the topic. Return "
    "queries only."
)


def _offline_queries(a: str, b: str, topic: str, syn: dict[str, list[str]]) -> list[str]:
    a_terms = " OR ".join(f'"{x}"' for x in [a, *syn.get(a, [])])
    b_terms = " OR ".join(f'"{x}"' for x in [b, *syn.get(b, [])])
    return [
        f'(({a_terms}) OR ({b_terms})) AND "{topic}"',
        f'({a_terms}) AND "{topic}"',
        f'({b_terms}) AND "{topic}"',
        f'(({a_terms}) AND ({b_terms})) AND ("{topic}" OR outcomes)',
    ]


class SearchAgent(Agent):
    key = "search"
    label = "Search Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        plan = state.research_plan or {}
        syn = plan.get("synonyms", {})
        model_used: str | None = None
        in_tok = out_tok = 0
        cost = 0.0
        primary_query: str | None = None

        if llm_live_enabled():
            try:
                syn_line = "; ".join(
                    f"{k}: {', '.join(v)}" for k, v in syn.items() if v
                ) or "none"
                res = await structured_call(
                    model=get_settings().model_agent,
                    system=_SYSTEM,
                    user=(
                        f"Molecule A: {a}\nMolecule B: {b}\nClinical topic: {t}\n"
                        f"Known synonyms: {syn_line}"
                    ),
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
            state.queries = _offline_queries(a, b, t, syn)

        # Retrieve (trusted-source allowlist + dedupe enforced in the registry).
        docs = await retrieve_evidence(a, b, t, sources=state.sources, query=primary_query)
        state.raw_docs = docs

        # Relevance embedding + evidence-tier ranking + top-k selection.
        top_k = get_settings().top_k_citations
        ranked: list[RankedDoc] = []
        if docs:
            texts = [f"{d.title}. {d.abstract}" for d in docs]
            doc_vecs = await embed_texts(texts)
            q_vec = await embed_query(f"{a} versus {b} for {t}")
            relevances = [cosine(q_vec, dv) for dv in doc_vecs]
            ranked = rank_docs(docs, relevances)[:top_k]
            vec_by_key = {
                d.dedup_key(): dv for d, dv in zip(docs, doc_vecs, strict=False)
            }
            for i, rd in enumerate(ranked):
                rd.ref_key = f"c{i + 1}"  # stable per-report id
                rd.metadata["embedding"] = vec_by_key.get(rd.doc.dedup_key(), [])

        state.ranked = ranked
        state.snapshot["queries"] = state.queries
        state.snapshot["candidates"] = len(docs)
        state.snapshot["ranked"] = len(ranked)

        return AgentOutcome(
            detail=(
                f"{len(state.queries)} queries -> {len(docs)} candidate(s); "
                f"ranked {len(ranked)}, top tier {top_tier_label(ranked).lower()}"
            ),
            model=model_used,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )
