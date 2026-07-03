"""Specialist evidence-extraction agents (Phase 4).

Each agent slices the verified evidence set into a clinical domain, attributes
documents to molecule A / B / both, and scores the domain with GRADE. These
structured findings feed the comparison engine and the section synthesizer so
the "Guideline / Trial / Meta-analysis / Safety" agents do real work rather than
only reporting progress.
"""

from app.agents.specialists import DomainResult, analyze, mentions

__all__ = ["DomainResult", "analyze", "mentions"]
