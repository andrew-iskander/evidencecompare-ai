from __future__ import annotations

import io
import re

from app.models.report import Export, Report

# (media_type, file extension) per export format.
EXPORT_MEDIA: dict[str, tuple[str, str]] = {
    "markdown": ("text/markdown; charset=utf-8", "md"),
    "pdf": ("application/pdf", "pdf"),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
    "pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "pptx",
    ),
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")
# Map common non-latin-1 glyphs so the PDF core font (Helvetica) can render them.
_UNI = {
    "–": "-", "—": "-", "‘": "'", "’": "'", "“": '"',
    "”": '"', "…": "...", "≥": ">=", "≤": "<=", "×": "x",
    "−": "-", "±": "+/-", "α": "alpha", "β": "beta",
    "γ": "gamma", "µ": "u", "°": "deg", "→": "->",
}


def _slug(report: Report) -> str:
    base = f"evidencecompare-{report.molecule_a}-vs-{report.molecule_b}"
    return _SLUG_RE.sub("-", base.lower()).strip("-") or "report"


def _ascii(s: str | None) -> str:
    if not s:
        return ""
    for k, v in _UNI.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


def _claim_text(claim: object) -> str:
    return claim.get("text", "") if isinstance(claim, dict) else str(claim)


def _claim_cids(claim: object) -> list:
    return claim.get("citation_ids", []) if isinstance(claim, dict) else []


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


def _render_pdf(report: Report) -> bytes:
    from fpdf import FPDF  # type: ignore[import-untyped]

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(text: str, h: float = 5.0) -> None:
        # new_x=LMARGIN returns the cursor to the left margin so the next
        # full-width multi_cell has room (avoids fpdf2's zero-width error).
        pdf.multi_cell(0, h, _ascii(text), new_x="LMARGIN", new_y="NEXT")

    def h2(title: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        line(title, 7)
        pdf.set_font("Helvetica", "", 10)

    pdf.set_font("Helvetica", "B", 16)
    line(f"{report.molecule_a} vs {report.molecule_b}", 9)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    line(f"Topic: {report.topic}", 6)
    if report.model_synthesis:
        line(f"Synthesis: {report.model_synthesis}", 6)
    pdf.set_text_color(0, 0, 0)

    ref_index = {c.ref_key: i + 1 for i, c in enumerate(report.citations)}

    if report.comparison_rows:
        h2("Side-by-side comparison")
        for row in report.comparison_rows:
            pdf.set_font("Helvetica", "B", 9)
            line(f"{row.attribute}  [{row.confidence}]")
            pdf.set_font("Helvetica", "", 9)
            line(f"  {report.molecule_a}: {row.value_a}")
            line(f"  {report.molecule_b}: {row.value_b}")
            if row.rationale:
                line(f"  Why: {row.rationale}")
            pdf.ln(1)

    for section in report.sections:
        h2(f"{section.title}  ({section.confidence})")
        for claim in section.claims:
            marks = "".join(f"[{ref_index.get(c, '?')}]" for c in _claim_cids(claim))
            line(f"- {_claim_text(claim)} {marks}".rstrip())
        pdf.ln(1)

    if report.citations:
        h2("References")
        pdf.set_font("Helvetica", "", 9)
        for i, c in enumerate(report.citations):
            bits = [c.title or "", c.source.upper()]
            if c.year:
                bits.append(str(c.year))
            if c.pmid:
                bits.append(f"PMID {c.pmid}")
            if c.doi:
                bits.append(f"DOI {c.doi}")
            line(f"{i + 1}. " + " | ".join(bits))

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    line(
        "Decision-support only. Not a diagnostic device or a substitute for "
        "professional clinical judgment.",
        4,
    )
    return bytes(pdf.output())


def _render_xlsx(report: Report) -> bytes:
    from openpyxl import Workbook  # type: ignore[import-untyped]

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append(["EvidenceCompare AI"])
    ws.append(["Molecule A", report.molecule_a])
    ws.append(["Molecule B", report.molecule_b])
    ws.append(["Topic", report.topic])
    ws.append(["Synthesis", report.model_synthesis or ""])
    ws.append(["Status", report.status])

    cw = wb.create_sheet("Comparison")
    cw.append(["Attribute", report.molecule_a, report.molecule_b, "Confidence", "Rationale"])
    for row in report.comparison_rows:
        cw.append([row.attribute, row.value_a, row.value_b, row.confidence, row.rationale or ""])

    if report.extractions:
        ew = wb.create_sheet("Extractions")
        ew.append([
            "Ref", "Title", "Design", "Population", "Intervention", "Comparator",
            "N", "HR", "RR", "95% CI", "p", "Adverse events",
        ])
        for e in report.extractions:
            ew.append([
                e.ref_key, e.title, e.study_design or "", e.population or "",
                e.intervention or "", e.comparator or "", e.sample_size or "",
                e.hazard_ratio or "", e.relative_risk or "", e.confidence_interval or "",
                e.p_value or "", ", ".join(e.adverse_events or []),
            ])

    rw = wb.create_sheet("References")
    rw.append(["#", "Title", "Source", "Year", "PMID", "DOI", "Verified"])
    for i, c in enumerate(report.citations):
        rw.append([
            i + 1, c.title, c.source, c.year or "", c.pmid or "", c.doi or "",
            "yes" if c.verified else "no",
        ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _render_pptx(report: Report) -> bytes:
    from pptx import Presentation  # type: ignore[import-untyped]

    prs = Presentation()
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = f"{report.molecule_a} vs {report.molecule_b}"
    title_slide.placeholders[1].text = f"{report.topic}  -  EvidenceCompare AI"

    def bullet_slide(title: str, lines: list[str]) -> None:
        if not lines:
            return
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        tf = slide.placeholders[1].text_frame
        tf.clear()
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line

    summary = [
        _claim_text(claim)
        for sec in report.sections
        if sec.layer == "clinical_summary"
        for claim in sec.claims
    ]
    bullet_slide("Clinical Summary", summary[:8])
    bullet_slide(
        "Side-by-side comparison",
        [
            f"{r.attribute} - {report.molecule_a}: {r.value_a} | "
            f"{report.molecule_b}: {r.value_b} ({r.confidence})"
            for r in report.comparison_rows
        ][:10],
    )
    bullet_slide(
        "References",
        [f"{i + 1}. {c.title} ({c.source.upper()})" for i, c in enumerate(report.citations)][:12],
    )

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def render_export(report: Report, fmt: str) -> tuple[bytes, str, str]:
    """Render a report to downloadable bytes. Returns (data, media_type, filename)."""
    media, ext = EXPORT_MEDIA[fmt]
    if fmt == "markdown":
        data = _render_markdown(report).encode("utf-8")
    elif fmt == "pdf":
        data = _render_pdf(report)
    elif fmt == "xlsx":
        data = _render_xlsx(report)
    elif fmt == "pptx":
        data = _render_pptx(report)
    else:  # pragma: no cover - schema restricts fmt
        raise ValueError(f"unsupported format: {fmt}")
    return data, media, f"{_slug(report)}.{ext}"


def build_export(report: Report, fmt: str) -> Export:
    """Record an export request. Markdown content is inlined; binary formats are
    generated on demand by the download endpoint via `render_export`."""
    content = _render_markdown(report) if fmt == "markdown" else None
    _, ext = EXPORT_MEDIA[fmt]
    return Export(
        report_id=report.id,
        format=fmt,
        status="ready",
        object_url=f"/api/v1/reports/{report.id}/download?format={fmt}",
        content=content,
    )
