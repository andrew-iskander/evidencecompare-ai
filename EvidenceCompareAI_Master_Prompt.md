# EvidenceCompare AI -- Master Build Prompt for Claude Code

## ROLE

You are an elite software architect, senior AI engineer, senior
full-stack developer, medical researcher, clinical pharmacologist,
cardiologist, UI/UX designer, and prompt engineer.

Your mission is to build a production-ready AI Medical Evidence
Intelligence Platform.

Do NOT jump into coding. Work in phases. At the end of each phase,
summarize decisions, update documentation, and continue only when the
phase is complete.

## PRODUCT GOAL

Build a premium web application inspired by modern AI SaaS dashboards
(similar in polish to the reference app supplied by the user) that
compares two pharmaceutical molecules for a user-defined clinical topic
using trustworthy evidence.

### Inputs

-   Molecule A
-   Molecule B
-   Clinical Topic

Example: A: Telmisartan B: Valsartan Topic: Cardioprotection

### Outputs

Produce an interactive evidence report including: - Executive summary -
Side-by-side comparison table - Mechanism of action - Guideline
recommendations - Randomized trials - Meta-analyses - Systematic
reviews - Safety - Contraindications - Drug interactions - Special
populations - Limitations - Evidence gaps - References with DOI/PMID -
Export to PDF, PPTX, Excel, Markdown

## TRUSTED DATA SOURCES

Use only reputable sources when retrieving evidence: - PubMed - Europe
PMC - Crossref - ClinicalTrials.gov - FDA - EMA - ACC - AHA - ESC -
KDIGO - ADA - NICE - WHO - Cochrane

Never fabricate citations. Clearly state when evidence is insufficient.

## PHASES

### Phase 0

Design: - Product requirements - System architecture - Tech stack -
Folder structure - Database schema - API specification - AI workflow -
CLAUDE.md - README

### Phase 1

Create frontend: - Next.js - React - TypeScript - Tailwind CSS -
shadcn/ui - Framer Motion

Premium UI with dark/light mode and responsive layout.

### Phase 2

Backend: - FastAPI - PostgreSQL - Redis - Authentication - User
accounts - Saved reports

### Phase 3

Evidence engine: - Retrieval Augmented Generation - Vector database -
Embeddings - Evidence ranking - Citation verification - Guideline parser

### Phase 4

Medical comparison engine: Generate comprehensive comparison tables with
confidence scoring.

### Phase 5

Visualizations: - Timelines - Evidence heatmaps - Risk-benefit matrix -
Evidence pyramid - Interactive expandable tables

### Phase 6

Testing: Unit, integration, end-to-end, accessibility, performance.

### Phase 7

Deployment: Docker, CI/CD, production configuration.

## UI

Create an Apple-quality interface with polished typography, spacing,
animations, and dashboards.

## AI AGENTS

Implement specialized agents: - Search - Guideline - Trial -
Meta-analysis - Safety - Evidence ranking - Citation verification -
Report generation

## DELIVERABLES

Generate: - Complete source code - Documentation - CLAUDE.md - README -
Architecture diagrams (Mermaid) - API docs - Sample data - Tests -
Deployment instructions

Continue until the application is production-ready. Keep code modular,
documented, and maintainable.
