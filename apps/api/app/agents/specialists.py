"""Domain specialist agents: classify, attribute, and GRADE evidence per domain.

Offline this is deterministic rule-based classification over the verified
`RankedDoc` set (study design + keyword hints); it never invents clinical
content, only characterizes the evidence that was actually retrieved. In live
mode the Report-Generation agent (Opus) extracts the clinical prose closed-book
over this same evidence, so the two paths stay consistent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.grade import GradeResult, grade
from app.rag.ranking import RankedDoc


def mentions(rd: RankedDoc, molecule: str) -> bool:
    """True if a document is about `molecule` (title/abstract or tagged metadata)."""
    m = molecule.lower()
    hay = f"{rd.doc.title} {rd.doc.abstract}".lower()
    mols = [str(x).lower() for x in rd.doc.metadata.get("molecules", [])]
    return m in hay or m in mols


# Canonical clinical domains. `designs` matches by study design; `keywords`
# additionally matches free text so e.g. an RCT abstract about interactions is
# picked up by the interactions agent too.
@dataclass(frozen=True)
class _DomainSpec:
    key: str
    title: str
    agent: str  # which pipeline agent owns this domain (for progress detail)
    designs: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


_DOMAINS: tuple[_DomainSpec, ...] = (
    _DomainSpec("mechanism_of_action", "Mechanism of Action", "search",
                keywords=("mechanism", "receptor", "agonist", "antagonist", "inhibit",
                          "pharmacodynam")),
    _DomainSpec("guidelines", "Guideline Recommendations", "guideline", designs=("guideline",)),
    _DomainSpec("trials", "Randomized Trials", "trial", designs=("rct", "trial_registry")),
    _DomainSpec("meta_analyses", "Meta-analyses & Systematic Reviews", "meta_analysis",
                designs=("meta_analysis", "systematic_review")),
    _DomainSpec("safety", "Safety", "safety", designs=("drug_label",),
                keywords=("safety", "adverse", "tolerab", "side effect")),
    _DomainSpec("contraindications", "Contraindications", "safety",
                keywords=("contraindicat", "warning", "boxed")),
    _DomainSpec("interactions", "Drug Interactions", "safety",
                keywords=("interaction", "co-administ", "coadminist", "concomitant")),
    _DomainSpec("special_populations", "Special Populations", "safety",
                keywords=("renal", "hepatic", "elderly", "geriatric", "pregnan",
                          "pediatric", "paediatric")),
)


@dataclass
class DomainResult:
    key: str
    title: str
    agent: str
    docs: list[RankedDoc] = field(default_factory=list)
    a_docs: list[RankedDoc] = field(default_factory=list)
    b_docs: list[RankedDoc] = field(default_factory=list)
    shared_docs: list[RankedDoc] = field(default_factory=list)

    @property
    def grade(self) -> GradeResult:
        return grade(self.docs)

    @property
    def confidence(self) -> str:
        return self.grade.level


def _matches(spec: _DomainSpec, rd: RankedDoc) -> bool:
    if rd.doc.study_design in spec.designs:
        return True
    if spec.keywords:
        hay = f"{rd.doc.title} {rd.doc.abstract}".lower()
        return any(k in hay for k in spec.keywords)
    return False


def analyze(
    molecule_a: str, molecule_b: str, verified: list[RankedDoc]
) -> dict[str, DomainResult]:
    """Classify verified evidence into clinical domains with molecule attribution."""
    results: dict[str, DomainResult] = {}
    for spec in _DOMAINS:
        docs = [rd for rd in verified if _matches(spec, rd)]
        a_docs = [rd for rd in docs if mentions(rd, molecule_a)]
        b_docs = [rd for rd in docs if mentions(rd, molecule_b)]
        shared = [rd for rd in docs if mentions(rd, molecule_a) and mentions(rd, molecule_b)]
        results[spec.key] = DomainResult(
            key=spec.key,
            title=spec.title,
            agent=spec.agent,
            docs=docs,
            a_docs=a_docs,
            b_docs=b_docs,
            shared_docs=shared,
        )
    return results


def head_to_head(verified: list[RankedDoc], molecule_a: str, molecule_b: str) -> list[RankedDoc]:
    """Trials that directly compare A vs B (both molecules in one trial-level doc)."""
    return [
        rd
        for rd in verified
        if rd.doc.study_design in ("rct", "trial_registry")
        and mentions(rd, molecule_a)
        and mentions(rd, molecule_b)
    ]
