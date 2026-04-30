"""
Veridian — PDF Export
----------------------
Generates a formatted PDF report with Veridian letterhead.
Uses reportlab for layout.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Colours ───────────────────────────────────────────────────────────────────
CREAM      = colors.HexColor("#F7F4EE")
CREAM_DARK = colors.HexColor("#EDE9E0")
INK        = colors.HexColor("#1A1714")
INK_SOFT   = colors.HexColor("#3D3830")
INK_MUTED  = colors.HexColor("#8C8479")
INK_FAINT  = colors.HexColor("#C4BFB6")
RUST       = colors.HexColor("#B5541C")
BORDER     = colors.HexColor("#E2DDD6")
INVEST     = colors.HexColor("#3D6B4F")
WATCH      = colors.HexColor("#8C6B1A")
PASS_COL   = colors.HexColor("#8C2A2A")
WHITE      = colors.white


def verdict_color(v):
    return {"INVEST": INVEST, "WATCH": WATCH, "PASS": PASS_COL}.get(v, WATCH)


def score_color(s):
    if s >= 7: return INVEST
    if s >= 5: return WATCH
    return PASS_COL


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica",
            fontSize=7, textColor=INK_MUTED, spaceAfter=4, leading=10,
            alignment=TA_LEFT),
        "company": ParagraphStyle("company", fontName="Helvetica-Bold",
            fontSize=28, textColor=INK, spaceAfter=4, leading=32),
        "one_liner": ParagraphStyle("one_liner", fontName="Helvetica-Oblique",
            fontSize=11, textColor=INK_MUTED, spaceAfter=8, leading=16),
        "tldr": ParagraphStyle("tldr", fontName="Helvetica",
            fontSize=10, textColor=INK_SOFT, spaceAfter=12, leading=16),
        "section_label": ParagraphStyle("section_label", fontName="Helvetica",
            fontSize=7, textColor=INK_MUTED, spaceAfter=6, leading=10),
        "body": ParagraphStyle("body", fontName="Helvetica",
            fontSize=9, textColor=INK_SOFT, spaceAfter=6, leading=14),
        "body_bold": ParagraphStyle("body_bold", fontName="Helvetica-Bold",
            fontSize=9, textColor=INK, spaceAfter=4, leading=14),
        "sub_label": ParagraphStyle("sub_label", fontName="Helvetica",
            fontSize=7, textColor=INK_FAINT, spaceAfter=3, leading=10),
        "list_item": ParagraphStyle("list_item", fontName="Helvetica",
            fontSize=9, textColor=INK_SOFT, spaceAfter=3, leading=13,
            leftIndent=12),
        "rec": ParagraphStyle("rec", fontName="Helvetica-Oblique",
            fontSize=10, textColor=INK, spaceAfter=0, leading=16),
        "footer": ParagraphStyle("footer", fontName="Helvetica",
            fontSize=7, textColor=INK_FAINT, alignment=TA_CENTER, leading=10),
        "score_num": ParagraphStyle("score_num", fontName="Helvetica-Bold",
            fontSize=20, textColor=INK, alignment=TA_CENTER, leading=24),
        "score_label": ParagraphStyle("score_label", fontName="Helvetica",
            fontSize=7, textColor=INK_MUTED, alignment=TA_CENTER, leading=10),
    }


def bullet(text: str, style) -> Paragraph:
    return Paragraph(f"→  {text}", style)


def hr(color=BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness,
                      color=color, spaceAfter=8, spaceBefore=4)


def section_header(title: str, styles: dict):
    return [
        Paragraph(title.upper(), styles["section_label"]),
        hr(),
    ]


# ── Main export function ──────────────────────────────────────────────────────
def generate_pdf(report: dict, rubric_weights: dict = None) -> bytes:
    """
    Generate a formatted PDF report.
    Returns PDF as bytes (for Streamlit download button).
    """
    buffer = io.BytesIO()
    W, H = A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"Veridian DD — {report.get('company_name','Report')}",
        author="Veridian AI Due Diligence",
    )

    styles = make_styles()
    story  = []

    company  = report.get("company_name", "Unknown")
    verdict  = report.get("verdict", "WATCH")
    conf     = report.get("confidence", "MEDIUM")
    tldr     = report.get("tldr", "")
    overall  = report.get("overall_score", 0)
    one_line = report.get("one_line_verdict", "")
    rec      = report.get("recommendation", "")
    sections = report.get("sections", {})
    market   = sections.get("market", {})
    team     = sections.get("team", {})
    product  = sections.get("product", {})
    traction = sections.get("traction", {})
    risks    = sections.get("risks", {})
    comps    = sections.get("comparables", {})
    qs       = sections.get("questions_to_ask", [])

    vcol = verdict_color(verdict)

    # ── Header ────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"VERIDIAN  ·  DUE DILIGENCE REPORT  ·  {datetime.now().strftime('%d %b %Y').upper()}",
        styles["eyebrow"]
    ))
    story.append(hr(RUST, 1.5))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(company, styles["company"]))
    story.append(Paragraph(f'"{one_line}"', styles["one_liner"]))

    # Verdict badge
    verdict_icon = {"INVEST": "◆", "WATCH": "◉", "PASS": "✕"}.get(verdict, "◉")
    story.append(Table(
        [[Paragraph(f"{verdict_icon}  {verdict}  ·  CONFIDENCE: {conf}",
                    ParagraphStyle("vbadge", fontName="Helvetica-Bold",
                                   fontSize=9, textColor=vcol))]],
        colWidths=[W - 40*mm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor(
                "#E8F0EB" if verdict=="INVEST" else "#F5EED8" if verdict=="WATCH" else "#F5E0E0")),
            ("BOX", (0,0), (-1,-1), 0.5, vcol),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
        ])
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(tldr, styles["tldr"]))
    story.append(hr())

    # ── Score grid ────────────────────────────────────────────────────
    score_items = [
        ("Market",   market.get("score", 0)),
        ("Team",     team.get("score", 0)),
        ("Product",  product.get("score", 0)),
        ("Traction", traction.get("score", 0)),
        ("Overall",  overall),
    ]

    score_data = [[
        Paragraph(str(s), ParagraphStyle("sn", fontName="Helvetica-Bold",
            fontSize=18, textColor=score_color(s), alignment=TA_CENTER))
        for _, s in score_items
    ], [
        Paragraph(l, styles["score_label"]) for l, _ in score_items
    ]]

    story.append(Table(
        score_data,
        colWidths=[(W - 40*mm) / 5] * 5,
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), CREAM),
            ("BOX", (0,0), (-1,-1), 0.5, BORDER),
            ("INNERGRID", (0,0), (-1,-1), 0.5, BORDER),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ])
    ))
    story.append(Spacer(1, 6*mm))

    # ── Two column sections ───────────────────────────────────────────
    def section_block(title: str, score: int, content: list) -> list:
        """Build a section block as a list of flowables."""
        items = []
        items.append(Paragraph(
            f"{title.upper()}  {score}/10",
            ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=8,
                           textColor=score_color(score), spaceAfter=4)
        ))
        items.extend(content)
        return items

    def risk_block(title: str, content: list) -> list:
        items = [Paragraph(title.upper(), ParagraphStyle("sh", fontName="Helvetica-Bold",
                fontSize=8, textColor=INK_MUTED, spaceAfter=4))]
        items.extend(content)
        return items

    # Market
    mkt_block = section_block("Market Opportunity", market.get("score",0), [
        Paragraph(market.get("summary",""), styles["body"]),
        Paragraph("SIZE", styles["sub_label"]),
        Paragraph(market.get("size_estimate",""), styles["body"]),
        Paragraph("TIMING", styles["sub_label"]),
        Paragraph(market.get("timing",""), styles["body"]),
    ])

    # Team
    team_flags = [bullet(f, styles["list_item"]) for f in team.get("red_flags",[])] or [Paragraph("None identified", styles["body"])]
    team_block = section_block("Team & Founder Fit", team.get("score",0), [
        Paragraph(team.get("summary",""), styles["body"]),
        Paragraph("FOUNDER-MARKET FIT", styles["sub_label"]),
        Paragraph(team.get("founder_market_fit",""), styles["body"]),
        Paragraph("RED FLAGS", styles["sub_label"]),
        *team_flags,
    ])

    # Product
    prod_block = section_block("Product & Differentiation", product.get("score",0), [
        Paragraph(product.get("summary",""), styles["body"]),
        Paragraph("DIFFERENTIATION", styles["sub_label"]),
        Paragraph(product.get("differentiation",""), styles["body"]),
        Paragraph("MOAT", styles["sub_label"]),
        Paragraph(product.get("moat",""), styles["body"]),
    ])

    # Traction
    sigs = [bullet(s, styles["list_item"]) for s in traction.get("signals",[])] or [Paragraph("None identified", styles["body"])]
    trac_block = section_block("Traction Signals", traction.get("score",0), [
        Paragraph(traction.get("summary",""), styles["body"]),
        Paragraph("EVIDENCE", styles["sub_label"]),
        *sigs,
        Paragraph("REAL VS CLAIMED", styles["sub_label"]),
        Paragraph(traction.get("what_is_real_vs_claimed",""), styles["body"]),
    ])

    # Risk
    top_risks = [bullet(r, styles["list_item"]) for r in risks.get("top_risks",[])] or [Paragraph("None", styles["body"])]
    mitigants = [bullet(m, styles["list_item"]) for m in risks.get("mitigants",[])] or [Paragraph("None", styles["body"])]
    deal_break = [bullet(d, styles["list_item"]) for d in risks.get("deal_breakers",[])] or [Paragraph("None", styles["body"])]
    risk_blk = risk_block("Risk Assessment", [
        Paragraph("TOP RISKS", styles["sub_label"]), *top_risks,
        Paragraph("MITIGANTS", styles["sub_label"]), *mitigants,
        Paragraph("DEAL BREAKERS", styles["sub_label"]), *deal_break,
    ])

    # Comparables
    sims  = [bullet(c, styles["list_item"]) for c in comps.get("similar_companies",[])] or [Paragraph("None", styles["body"])]
    exits = [bullet(e, styles["list_item"]) for e in comps.get("relevant_exits",[])] or [Paragraph("None", styles["body"])]
    comp_blk = risk_block("Comparables & Exits", [
        Paragraph("SIMILAR COMPANIES", styles["sub_label"]), *sims,
        Paragraph("RELEVANT EXITS", styles["sub_label"]), *exits,
        Paragraph("VALUATION ANCHOR", styles["sub_label"]),
        Paragraph(comps.get("valuation_anchor",""), styles["body"]),
    ])

    # Two-column table
    def to_col(items):
        col = []
        for item in items:
            if isinstance(item, list):
                col.extend(item)
            else:
                col.append(item)
        return col

    col_w = (W - 40*mm - 4*mm) / 2

    for left, right in [(mkt_block, team_block), (prod_block, trac_block), (risk_blk, comp_blk)]:
        story.append(Table(
            [[left, right]],
            colWidths=[col_w, col_w],
            style=TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (0,-1), 4*mm),
            ])
        ))
        story.append(Spacer(1, 4*mm))

    # ── Questions ─────────────────────────────────────────────────────
    if qs:
        story.extend(section_header("Questions to Ask the Founder", styles))
        for q in qs:
            story.append(bullet(q, styles["list_item"]))
        story.append(Spacer(1, 4*mm))

    # ── Recommendation ────────────────────────────────────────────────
    story.append(hr(RUST, 1))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("◆  VERIDIAN RECOMMENDATION", ParagraphStyle(
        "rl", fontName="Helvetica-Bold", fontSize=8, textColor=RUST, spaceAfter=6)))
    story.append(Paragraph(rec, styles["rec"]))
    story.append(Spacer(1, 6*mm))

    # ── Rubric weights (if custom) ────────────────────────────────────
    if rubric_weights:
        story.append(hr())
        story.append(Paragraph("CUSTOM SCORING RUBRIC", styles["section_label"]))
        weights_text = "  ·  ".join(
            f"{k.title()}: {int(v*100)}%" for k, v in rubric_weights.items()
        )
        story.append(Paragraph(weights_text, styles["body"]))
        story.append(Spacer(1, 4*mm))

    # ── Footer ────────────────────────────────────────────────────────
    story.append(hr(INK_FAINT, 0.5))
    story.append(Paragraph(
        f"VERIDIAN  ·  AI DUE DILIGENCE  ·  CONFIDENTIAL  ·  {datetime.now().strftime('%d %b %Y %H:%M')}",
        styles["footer"]
    ))

    doc.build(story)
    return buffer.getvalue()
