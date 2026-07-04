import type { AgentProgress, Report } from "@/types/report";

/**
 * Sample data for Phase 1 (frontend before backend). Illustrative only — NOT a
 * source of medical truth. Real reports come from the RAG evidence engine with
 * verified citations.
 */

export const AGENTS: AgentProgress[] = [
  { key: "search", label: "Search Agent", state: "pending" },
  { key: "ranking", label: "Evidence-Ranking Agent", state: "pending" },
  { key: "extraction", label: "Trial-Extraction Agent", state: "pending" },
  { key: "guideline", label: "Guideline Agent", state: "pending" },
  { key: "comparison", label: "Comparison Agent", state: "pending" },
  { key: "writer", label: "Medical-Writer Agent", state: "pending" },
];

export const SAMPLE_REPORT: Report = {
  id: "demo",
  status: "complete",
  moleculeA: "Telmisartan",
  moleculeB: "Valsartan",
  topic: "Cardioprotection",
  costUsd: 0.42,
  freshness: "up_to_date",
  moleculeEvidence: {
    a: { efficacy: 2, safety: 1, guideline: 1 },
    b: { efficacy: 1, safety: 1, guideline: 1 },
  },
  extractions: [
    {
      refKey: "c1",
      title:
        "Telmisartan, ramipril, or both in patients at high risk for vascular events (ONTARGET)",
      studyDesign: "rct",
      population: "High-risk adults with vascular disease or diabetes",
      intervention: "Telmisartan",
      comparator: "Ramipril",
      sampleSize: 25620,
      outcomes: ["CV death, MI, stroke, or HF hospitalization"],
      hazardRatio: "HR 1.01",
      relativeRisk: undefined,
      confidenceInterval: "95% CI 0.94-1.09",
      pValue: "p=0.004 (non-inferiority)",
      adverseEvents: ["Hypotension", "Syncope"],
      strengths: ["Randomized design", "Large sample size", "Hard CV outcomes"],
      limitations: ["Comparator is an ACE inhibitor, not the other ARB"],
      extractorModel: "sample",
    },
    {
      refKey: "c2",
      title:
        "Effects of valsartan on morbidity and mortality in heart failure (Val-HeFT)",
      studyDesign: "rct",
      population: "Adults with NYHA II-IV chronic heart failure",
      intervention: "Valsartan",
      comparator: "Placebo (on background therapy)",
      sampleSize: 5010,
      outcomes: ["All-cause mortality", "Morbidity (HF hospitalization)"],
      hazardRatio: undefined,
      relativeRisk: "RR 0.87 (combined endpoint)",
      confidenceInterval: "95% CI 0.79-0.96",
      pValue: "p=0.009",
      adverseEvents: ["Hyperkalemia", "Hypotension", "Renal dysfunction"],
      strengths: ["Randomized design", "Placebo-controlled"],
      limitations: ["Heart-failure population differs from ONTARGET"],
      extractorModel: "sample",
    },
  ],
  citations: [
    {
      id: "c1",
      title:
        "Telmisartan, ramipril, or both in patients at high risk for vascular events (ONTARGET)",
      source: "pubmed",
      studyDesign: "rct",
      pmid: "18378520",
      doi: "10.1056/NEJMoa0801317",
      year: 2008,
      verified: true,
    },
    {
      id: "c2",
      title:
        "Effects of valsartan on morbidity and mortality in heart failure (Val-HeFT)",
      source: "pubmed",
      studyDesign: "rct",
      pmid: "11759645",
      doi: "10.1056/NEJMoa010713",
      year: 2001,
      verified: true,
    },
    {
      id: "c3",
      title:
        "2023 ESC Guidelines for the management of cardiovascular disease",
      source: "esc",
      studyDesign: "guideline",
      year: 2023,
      verified: true,
    },
  ],
  comparison: [
    {
      attribute: "Drug class",
      valueA: "ARB (angiotensin II receptor blocker)",
      valueB: "ARB (angiotensin II receptor blocker)",
      confidence: "high",
      rationale:
        "High certainty from a current practice guideline classing both agents.",
      citationIds: ["c3"],
    },
    {
      attribute: "Plasma half-life",
      valueA: "~24 h (long)",
      valueB: "~6 h (short–intermediate)",
      confidence: "high",
      rationale:
        "Consistent pharmacokinetic reporting across two randomized trials.",
      citationIds: ["c1", "c2"],
    },
    {
      attribute: "Landmark CV outcome trial",
      valueA: "ONTARGET (high-risk vascular events)",
      valueB: "Val-HeFT (heart failure)",
      confidence: "high",
      rationale:
        "Each molecule has a large, well-powered outcome RCT — but in different populations.",
      citationIds: ["c1", "c2"],
    },
    {
      attribute: "PPAR-γ partial agonism (metabolic effect)",
      valueA: "Yes — reported",
      valueB: "Not established",
      confidence: "moderate",
      rationale:
        "Reported for one molecule in a single trial; not evaluated for the other.",
      citationIds: ["c1"],
    },
    {
      attribute: "Head-to-head CV mortality difference",
      valueA: "Insufficient direct comparative evidence",
      valueB: "Insufficient direct comparative evidence",
      confidence: "very_low",
      rationale: "No retrieved trial compares the two molecules head-to-head.",
      citationIds: [],
    },
  ],
  sections: [
    {
      key: "executive_summary",
      title: "Executive Summary",
      confidence: "moderate",
      claims: [
        {
          text: "Both telmisartan and valsartan are angiotensin II receptor blockers used across hypertension and cardiovascular-risk indications.",
          citationIds: ["c3"],
        },
        {
          text: "Telmisartan has a notably longer half-life (~24 h), supporting sustained 24-hour blood-pressure control.",
          citationIds: ["c1"],
        },
        {
          text: "Direct head-to-head trials powered for hard cardiovascular outcomes between the two agents are limited.",
          citationIds: [],
        },
      ],
    },
    {
      key: "mechanism_of_action",
      title: "Mechanism of Action",
      confidence: "high",
      claims: [
        {
          text: "Both selectively block the angiotensin II type-1 (AT1) receptor, reducing vasoconstriction and aldosterone-driven sodium retention.",
          citationIds: ["c3"],
        },
        {
          text: "Telmisartan additionally shows partial PPAR-γ agonism, a proposed metabolic mechanism not established for valsartan.",
          citationIds: ["c1"],
        },
      ],
    },
    {
      key: "guidelines",
      title: "Guideline Recommendations",
      confidence: "moderate",
      claims: [
        {
          text: "Major guidelines position ARBs as first-line options for hypertension and for RAAS blockade where ACE inhibitors are not tolerated.",
          citationIds: ["c3"],
        },
      ],
    },
    {
      key: "trials",
      title: "Randomized Trials",
      confidence: "high",
      claims: [
        {
          text: "ONTARGET established telmisartan as non-inferior to ramipril for cardiovascular outcomes in high-risk patients.",
          citationIds: ["c1"],
        },
        {
          text: "Val-HeFT demonstrated valsartan's benefit on morbidity in chronic heart failure.",
          citationIds: ["c2"],
        },
      ],
    },
    {
      key: "safety",
      title: "Safety",
      confidence: "moderate",
      claims: [
        {
          text: "Class effects include hyperkalemia, hypotension, and renal function changes; monitoring is advised in at-risk populations.",
          citationIds: ["c3"],
        },
      ],
    },
    {
      key: "evidence_gaps",
      title: "Evidence Gaps",
      confidence: "very_low",
      insufficientEvidence: true,
      claims: [
        {
          text: "No adequately powered direct head-to-head trial comparing telmisartan and valsartan on hard cardiovascular endpoints was identified in this snapshot.",
          citationIds: [],
        },
      ],
    },
  ],
};
