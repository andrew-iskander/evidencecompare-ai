from __future__ import annotations

from app.models.report import Export, Report


def _render_markdown(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"# EvidenceCompare AI — {report.molecule_a} vs {report.molecule_b}")
    lines.append("")
    lines.append(f"**Topic:** {report.topic}  ")
    lines.append(f"**Status:** {report.status}  ")
    if report.model_synthesis:
        lines.append(f"**Synthesis model:** {report.model_synthesis}  ")
    lines.append("")

    if report.comparison_rows:
        lines.append("## Side-by-side comparison")
        lines.append("")
        lines.append(
            f"| Attribute | {report.molecule_a} | {report.molecule_b} | Confidence | Rationale |"
        )
        lines.append("|---|---|---|---|---|")
        for row in report.comparison_rows:
            rationale = (row.rationale or "").replace("|", "\\|")
            lines.append(
                f"| {row.attribute} | {row.value_a} | {row.value_b} "
                f"| {row.confidence} | {rationale} |"
            )
        lines.append("")

    ref_index = {c.ref_key: i + 1 for i, c in enumerate(report.citations)}

    for section in report.sections:
        lines.append(f"## {section.title}")
        flag = " _(insufficient evidence)_" if section.insufficient_evidence else ""
        lines.append(f"_Confidence: {section.confidence}{flag}_")
        lines.append("")
        for claim in section.claims:
            cids = claim.get("citation_ids", []) if isinstance(claim, dict) else []
            marks = "".join(f"[{ref_index.get(cid, '?')}]" for cid in cids)
            text = claim.get("text", "") if isinstance(claim, dict) else str(claim)
            suffix = f" {marks}" if marks else " _(unsourced)_"
            lines.append(f"- {text}{suffix}")
        lines.append("")

    if report.citations:
        lines.append("## References")
        lines.append("")
        for i, c in enumerate(report.citations):
            bits = [c.title, c.source.upper()]
            if c.year:
                bits.append(str(c.year))
            if c.pmid:
                bits.append(f"PMID {c.pmid}")
            if c.doi:
                bits.append(f"DOI {c.doi}")
            verified = " (verified)" if c.verified else ""
            lines.append(f"{i + 1}. {' · '.join(bits)}{verified}")
        lines.append("")

    lines.append(
        "> Decision-support only. Not a diagnostic device or a substitute for "
        "professional clinical judgment."
    )
    return "\n".join(lines)


def build_export(report: Report, fmt: str) -> Export:
    """Phase 2: markdown is rendered inline. Binary formats (pdf/pptx/xlsx) are
    recorded and marked ready with a note; real rendering lands in Phase 7."""
    if fmt == "markdown":
        return Export(
            report_id=report.id,
            format=fmt,
            status="ready",
            content=_render_markdown(report),
        )
    return Export(
        report_id=report.id,
        format=fmt,
        status="ready",
        object_url=f"/exports/{report.id}.{fmt}",
        content=None,
    )
