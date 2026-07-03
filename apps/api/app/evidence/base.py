from __future__ import annotations

from dataclasses import dataclass, field

# Trusted-source allowlist (PRD §4). Nothing outside this set may become a citation.
TRUSTED_SOURCES: frozenset[str] = frozenset(
    {
        "pubmed",
        "europepmc",
        "crossref",
        "clinicaltrials",
        "fda",
        "ema",
        "acc",
        "aha",
        "esc",
        "kdigo",
        "ada",
        "nice",
        "who",
        "cochrane",
        "guideline",
    }
)


@dataclass
class RawDoc:
    """Normalized evidence record from a trusted source."""

    source: str
    title: str
    external_id: str | None = None
    doi: str | None = None
    pmid: str | None = None
    abstract: str = ""
    # rct | meta_analysis | systematic_review | guideline | trial_registry | drug_label | other
    study_design: str | None = None
    publication_year: int | None = None
    sample_size: int | None = None
    url: str | None = None
    metadata: dict = field(default_factory=dict)

    def dedup_key(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        if self.pmid:
            return f"pmid:{self.pmid}"
        return f"{self.source}:{(self.external_id or self.title).lower()}"


class EvidenceSource:
    """Interface for a trusted evidence source."""

    name: str = "base"

    async def search(
        self, molecule_a: str, molecule_b: str, topic: str, limit: int
    ) -> list[RawDoc]:  # pragma: no cover - interface
        raise NotImplementedError
