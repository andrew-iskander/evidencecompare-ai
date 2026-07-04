from __future__ import annotations

from app.evidence.base import EvidenceSource, RawDoc

# Deterministic local evidence used when EVIDENCE_MODE=offline (no network / keys).
# This is synthetic scaffolding that flows through the SAME real ranking,
# verification, and synthesis path as live evidence — so the whole engine is
# exercisable and testable offline. It is clearly marked synthetic and is NOT a
# source of medical truth.


class OfflineSource(EvidenceSource):
    name = "offline"

    async def search(
        self,
        molecule_a: str,
        molecule_b: str,
        topic: str,
        limit: int,
        query: str | None = None,
    ) -> list[RawDoc]:
        a, b, t = molecule_a, molecule_b, topic
        docs = [
            RawDoc(
                source="pubmed",
                title=f"Randomized controlled trial of {a} for {t}",
                pmid="30000001",
                doi="10.0000/offline.a.rct",
                abstract=(
                    f"A randomized, double-blind, placebo-controlled trial evaluating {a} "
                    f"in the context of {t}. Adults with the target condition were randomized "
                    f"to {a} versus placebo. For the primary composite endpoint the hazard "
                    f"ratio was HR 0.86 (95% CI 0.75-0.98; p=0.03) favoring {a}. "
                    f"The most common adverse events were hypotension and dizziness."
                ),
                study_design="rct",
                publication_year=2019,
                sample_size=2400,
                metadata={"synthetic": True, "molecules": [a]},
            ),
            RawDoc(
                source="pubmed",
                title=f"Randomized controlled trial of {b} for {t}",
                pmid="30000002",
                doi="10.0000/offline.b.rct",
                abstract=(
                    f"A randomized, active-controlled trial evaluating {b} in the context "
                    f"of {t}. Participants received {b} or standard of care. The primary "
                    f"outcome relative risk was RR 0.91 (95% CI 0.82-1.01; p=0.08), "
                    f"a non-significant trend. Reported adverse events included "
                    f"hyperkalemia and headache."
                ),
                study_design="rct",
                publication_year=2020,
                sample_size=1800,
                metadata={"synthetic": True, "molecules": [b]},
            ),
            RawDoc(
                source="europepmc",
                title=f"Meta-analysis of outcomes for {t}",
                pmid="30000003",
                doi="10.0000/offline.meta",
                abstract=(
                    f"A meta-analysis pooling trials relevant to {t}, including agents "
                    f"such as {a} and {b}."
                ),
                study_design="meta_analysis",
                publication_year=2022,
                sample_size=15000,
                metadata={"synthetic": True, "molecules": [a, b]},
            ),
            RawDoc(
                source="guideline",
                title=f"Clinical practice guideline addressing {t}",
                doi="10.0000/offline.guideline",
                abstract=(
                    f"Guideline recommendations relevant to {t} and the drug class of {a} and {b}."
                ),
                study_design="guideline",
                publication_year=2023,
                metadata={"synthetic": True, "molecules": [a, b]},
            ),
            RawDoc(
                source="fda",
                title=f"Drug label safety information for {a}",
                external_id="offline-label-a",
                abstract=f"Safety, contraindications, and interactions for {a}.",
                study_design="drug_label",
                publication_year=2021,
                metadata={"synthetic": True, "molecules": [a]},
            ),
        ]
        return docs[:limit]
