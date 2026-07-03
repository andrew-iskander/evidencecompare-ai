# EvidenceCompare AI — Product Requirements Document (PRD)

**Phase:** 0 (Design) · **Status:** Draft · **Last updated:** 2026-07-03

---

## 1. Vision

EvidenceCompare AI is a premium web application that compares **two pharmaceutical
molecules** for a **user-defined clinical topic** using only trustworthy medical
evidence, and produces an interactive, exportable evidence report. It is built for
clinicians, pharmacologists, medical researchers, and formulary/HTA decision-makers
who need a defensible, citation-backed comparison quickly.

**North-star principle:** *Never fabricate citations. Clearly state when evidence is
insufficient.* Every substantive claim in a report must trace to a retrieved source
(DOI / PMID / registry ID / guideline reference).

---

## 2. Target users & personas

| Persona | Need | Success looks like |
|---|---|---|
| Cardiologist / clinician | Fast, trustworthy head-to-head at point of decision | Reads exec summary + comparison table in < 2 min, drills into trials |
| Clinical pharmacologist | Mechanism, PK/PD, interactions, special populations | Confidence-scored, source-linked pharmacology sections |
| Medical researcher | Evidence landscape, gaps, meta-analyses | Evidence pyramid + gap analysis + exportable references |
| HTA / formulary reviewer | Guideline positions, safety, defensible export | PPTX/PDF/Excel export with full citation list |

---

## 3. Inputs & outputs

### Inputs
- **Molecule A** (e.g. Telmisartan)
- **Molecule B** (e.g. Valsartan)
- **Clinical Topic** (e.g. Cardioprotection)
- Optional: patient population qualifier, date range, source filters.

### Outputs — the interactive evidence report
1. Executive summary
2. Side-by-side comparison table (with confidence scores)
3. Mechanism of action
4. Guideline recommendations (ACC/AHA/ESC/KDIGO/ADA/NICE/WHO/Cochrane)
5. Randomized trials
6. Meta-analyses
7. Systematic reviews
8. Safety
9. Contraindications
10. Drug interactions
11. Special populations (renal, hepatic, pregnancy, elderly, pediatric)
12. Limitations
13. Evidence gaps
14. References with DOI/PMID
15. Exports: **PDF, PPTX, Excel, Markdown**

---

## 4. Trusted data sources (allowlist)

Retrieval is **restricted** to: PubMed, Europe PMC, Crossref, ClinicalTrials.gov,
FDA (openFDA), EMA, ACC, AHA, ESC, KDIGO, ADA, NICE, WHO, Cochrane.

Any content outside this allowlist is excluded from evidence and citations.

---

## 5. Functional requirements

- **FR-1** Accept A/B/topic and validate molecules against a normalized drug vocabulary (RxNorm/ATC where available).
- **FR-2** Retrieve candidate evidence from trusted sources, deduplicate by DOI/PMID.
- **FR-3** Rank & filter evidence by study design, recency, sample size, and relevance.
- **FR-4** Verify every citation resolves to a real record before it appears in a report.
- **FR-5** Generate each report section with per-claim source attribution.
- **FR-6** Assign a **confidence score** (e.g. GRADE-inspired: High/Moderate/Low/Very Low) per comparison row and section.
- **FR-7** Render interactive visualizations (timeline, evidence heatmap, risk-benefit matrix, evidence pyramid, expandable tables).
- **FR-8** Export to PDF, PPTX, Excel, Markdown with citations intact.
- **FR-9** User accounts: sign up, log in, save/reopen/share reports.
- **FR-10** Show "insufficient evidence" states explicitly rather than hallucinating.
- **FR-11** Stream report generation progress to the UI (per-agent status).

## 6. Non-functional requirements

- **Trust & safety:** zero fabricated citations; every claim source-linked; medical
  disclaimer surfaced (decision-support, not a substitute for clinical judgment).
- **Performance:** first meaningful section streamed < 15 s; full report typically
  < 3 min; cached comparisons served < 2 s.
- **Accessibility:** WCAG 2.1 AA; keyboard navigable; dark/light themes.
- **Responsive:** desktop-first, usable on tablet.
- **Security:** JWT auth, hashed passwords (argon2/bcrypt), rate limiting, secrets in
  env/secret manager, no PII beyond account email.
- **Observability:** structured logs, per-agent tracing, token/cost accounting per report.
- **Reproducibility:** each report stores its retrieval snapshot + model + prompt version.

## 7. Explicit non-goals (v1)

- Not a diagnostic device; not for individual patient treatment decisions.
- No more than two molecules per comparison (v1).
- No real-time EHR integration.
- No fine-tuned/self-hosted LLM — uses the Claude API + Voyage embeddings.

## 8. Compliance & disclaimer

- Persistent medical disclaimer on every report and export.
- Store source licensing notes; respect each API's terms and rate limits.
- Cache upstream records where the source license permits; otherwise store IDs + links only.

## 9. Acceptance criteria (v1 "done")

- Given A=Telmisartan, B=Valsartan, Topic=Cardioprotection, the app returns a full
  report where **100% of citations resolve** to real PubMed/Crossref/registry records,
  each comparison row carries a confidence score, and the report exports cleanly to all
  four formats. Insufficient-evidence sections are labeled, not fabricated.
