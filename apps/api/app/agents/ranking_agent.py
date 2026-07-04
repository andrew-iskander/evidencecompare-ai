"""Evidence-Ranking Agent — embeds, scores evidence quality, and verifies citations.

Quality scoring is the GRADE-inspired composite (design tier, recency, size,
topical relevance) from `app.rag.ranking`/`app.rag.grade` — one scorer for the
whole app. This agent also runs citation verification so only resolvable sources
survive into the report. Deterministic and offline-safe (embeddings fall back to
a hashed bag-of-words when no Voyage key is present).
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.core.config import get_settings
from app.pipeline.comparison import top_tier_label
from app.rag.embeddings import cosine, embed_query, embed_texts
from app.rag.ranking import RankedDoc, rank_docs
from app.rag.verifier import verify_doc


class EvidenceRankingAgent(Agent):
    key = "ranking"
    label = "Evidence-Ranking Agent"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        docs = state.raw_docs
        if not docs:
            state.ranked = []
            state.verified = []
            return AgentOutcome(detail="no candidates to rank")

        a, b, t = state.molecule_a, state.molecule_b, state.topic
        top_k = get_settings().top_k_citations

        texts = [f"{d.title}. {d.abstract}" for d in docs]
        doc_vecs = await embed_texts(texts)
        q_vec = await embed_query(f"{a} versus {b} for {t}")
        relevances = [cosine(q_vec, dv) for dv in doc_vecs]
        ranked: list[RankedDoc] = rank_docs(docs, relevances)[:top_k]

        # Stash each selected doc's embedding for the engine to persist as a chunk.
        vec_by_key = {d.dedup_key(): dv for d, dv in zip(docs, doc_vecs, strict=False)}
        for rd in ranked:
            rd.metadata["embedding"] = vec_by_key.get(rd.doc.dedup_key(), [])
        state.ranked = ranked

        # Verify every citation; only resolvable ones survive. Re-key contiguously.
        verified = [rd for rd in ranked if await verify_doc(rd.doc)]
        for i, rd in enumerate(verified):
            rd.ref_key = f"c{i + 1}"
        state.verified = verified

        state.snapshot["ranked"] = len(ranked)
        state.snapshot["verified"] = len(verified)
        return AgentOutcome(
            detail=(
                f"ranked {len(ranked)}, verified {len(verified)}; "
                f"top tier {top_tier_label(verified).lower()}"
            )
        )
