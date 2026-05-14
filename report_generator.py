"""
GridMind-AI Report Generator
Investor-grade PDF and Markdown analytical reports for energy markets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand palette ─────────────────────────────────────────────────────────────

NAVY          = colors.HexColor("#1A2B4A")
ELECTRIC_BLUE = colors.HexColor("#2E86DE")
GREEN         = colors.HexColor("#27AE60")
AMBER         = colors.HexColor("#F39C12")
RED           = colors.HexColor("#C0392B")
LIGHT_GRAY    = colors.HexColor("#F5F7FA")
MID_GRAY      = colors.HexColor("#8E9BAA")
DARK_TEXT     = colors.HexColor("#2C3E50")
WHITE         = colors.white

HEX_NAVY  = "#1A2B4A"
HEX_BLUE  = "#2E86DE"
HEX_GREEN = "#27AE60"
HEX_AMBER = "#F39C12"
HEX_RED   = "#C0392B"
HEX_GRAY  = "#8E9BAA"

# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class ArbitrageInsight:
    window:      str    # e.g. "02:00–06:00 EST"
    spread_mwh:  float  # $/MWh spread
    confidence:  float  # 0.0–1.0
    direction:   str    # "charge" | "discharge"
    notes:       str = ""


@dataclass
class BatteryRecommendation:
    action:      str    # "Charge" | "Discharge" | "Hold"
    time_window: str    # e.g. "22:00–02:00 EST"
    soc_pct:     float  # target state-of-charge %
    rationale:   str


@dataclass
class VolatilityMetrics:
    period:           str
    mean_price:       float
    std_dev:          float
    min_price:        float
    max_price:        float
    volatility_index: float  # normalised 0–100


@dataclass
class KeyFinding:
    title:  str
    detail: str
    impact: str  # "high" | "medium" | "low"


@dataclass
class ReportData:
    title:                  str
    market:                 str           # e.g. "ERCOT Day-Ahead"
    date_range:             str           # e.g. "2026-05-10 – 2026-05-14"
    generated_at:           datetime
    executive_summary:      str
    key_findings:           list[KeyFinding]
    arbitrage_insights:     list[ArbitrageInsight]
    battery_recommendations: list[BatteryRecommendation]
    volatility_metrics:     list[VolatilityMetrics]
    total_arbitrage_value:  float
    currency:               str   = "USD"
    confidence_score:       float = 0.0   # 0–1
    subtitle:               str   = ""


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_currency(value: float, currency: str) -> str:
    return f"{currency} {value:,.2f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _impact_hex(impact: str) -> str:
    return {
        "high":   HEX_RED,
        "medium": HEX_AMBER,
        "low":    HEX_GREEN,
    }.get(impact.lower(), HEX_NAVY)


def _impact_color(impact: str) -> colors.Color:
    return {
        "high":   RED,
        "medium": AMBER,
        "low":    GREEN,
    }.get(impact.lower(), DARK_TEXT)


def _confidence_hex(conf: float) -> str:
    if conf >= 0.75:
        return HEX_GREEN
    if conf >= 0.50:
        return HEX_AMBER
    return HEX_RED


def _vi_hex(vi: float) -> str:
    if vi >= 70:
        return HEX_RED
    if vi >= 40:
        return HEX_AMBER
    return HEX_GREEN


# ── Paragraph styles ──────────────────────────────────────────────────────────

def _styles() -> dict:
    return {
        "cover_brand": ParagraphStyle(
            "cover_brand",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=ELECTRIC_BLUE,
            leading=16,
            spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=26,
            textColor=WHITE,
            leading=32,
            spaceAfter=6,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            fontName="Helvetica",
            fontSize=13,
            textColor=colors.HexColor("#A8C4E0"),
            leading=18,
            spaceAfter=20,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=10,
            textColor=MID_GRAY,
            leading=14,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=NAVY,
            leading=20,
            spaceBefore=12,
            spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=ELECTRIC_BLUE,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=DARK_TEXT,
            leading=15,
            spaceAfter=5,
        ),
        "finding_title": ParagraphStyle(
            "finding_title",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=NAVY,
            leading=14,
        ),
        "finding_detail": ParagraphStyle(
            "finding_detail",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK_TEXT,
            leading=13,
            leftIndent=10,
        ),
        "th": ParagraphStyle(
            "th",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WHITE,
            leading=12,
        ),
        "td": ParagraphStyle(
            "td",
            fontName="Helvetica",
            fontSize=9,
            textColor=DARK_TEXT,
            leading=12,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MID_GRAY,
            leading=11,
            spaceAfter=4,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=GREEN,
            leading=20,
        ),
        "kpi_conf": ParagraphStyle(
            "kpi_conf",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=ELECTRIC_BLUE,
            leading=20,
        ),
        "kpi_market": ParagraphStyle(
            "kpi_market",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=NAVY,
            leading=18,
        ),
    }


# ── Page layout callbacks ─────────────────────────────────────────────────────

class _PageLayout:
    def __init__(self, market: str):
        self.market = market

    def first_page(self, canvas, doc):
        w, h = A4
        canvas.saveState()
        # Full dark background
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, h, fill=True, stroke=False)
        # Top accent bar
        canvas.setFillColor(ELECTRIC_BLUE)
        canvas.rect(0, h - 0.55 * cm, w, 0.55 * cm, fill=True, stroke=False)
        # Bottom accent strip
        canvas.setFillColor(ELECTRIC_BLUE)
        canvas.rect(0, 0, w, 0.35 * cm, fill=True, stroke=False)
        # Left vertical design accent
        canvas.setFillColor(ELECTRIC_BLUE)
        canvas.rect(2.0 * cm, h * 0.32, 0.3 * cm, h * 0.48, fill=True, stroke=False)
        canvas.restoreState()

    def later_pages(self, canvas, doc):
        w, h = A4
        canvas.saveState()
        # Header bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 1.15 * cm, w, 1.15 * cm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(2 * cm, h - 0.65 * cm, "GRIDMIND-AI")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawRightString(w - 2 * cm, h - 0.65 * cm, self.market)
        # Footer
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.line(2 * cm, 1.7 * cm, w - 2 * cm, 1.7 * cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(2 * cm, 1.1 * cm, "CONFIDENTIAL — GridMind-AI Analytical Report")
        canvas.drawRightString(w - 2 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.restoreState()


# ── PDF section builders ──────────────────────────────────────────────────────

# Available content width: A4(21cm) - 2*2.5cm margins = 16cm
_W = 16.0 * cm


def _section_rule(color: colors.Color = ELECTRIC_BLUE) -> HRFlowable:
    return HRFlowable(width="100%", thickness=1, color=color, spaceAfter=8)


def _build_cover(data: ReportData, s: dict) -> list:
    return [
        Spacer(1, 6.5 * cm),
        Paragraph("GRIDMIND-AI", s["cover_brand"]),
        Spacer(1, 0.4 * cm),
        Paragraph(data.title, s["cover_title"]),
        *(
            [Paragraph(data.subtitle, s["cover_subtitle"])]
            if data.subtitle else [Spacer(1, 0.6 * cm)]
        ),
        Spacer(1, 0.8 * cm),
        Paragraph(f"Market: {data.market}", s["cover_meta"]),
        Paragraph(f"Period: {data.date_range}", s["cover_meta"]),
        Paragraph(
            f"Generated: {data.generated_at.strftime('%B %d, %Y  %H:%M UTC')}",
            s["cover_meta"],
        ),
        Paragraph(
            f"Model Confidence: {_fmt_pct(data.confidence_score)}",
            s["cover_meta"],
        ),
        PageBreak(),
    ]


def _build_executive_summary(data: ReportData, s: dict) -> list:
    elems: list = [
        Paragraph("Executive Summary", s["h1"]),
        _section_rule(),
    ]

    # Highlighted summary box
    box = Table(
        [[Paragraph(data.executive_summary, s["body"])]],
        colWidths=[_W],
    )
    box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX",           (0, 0), (-1, -1), 0.8, ELECTRIC_BLUE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elems.append(box)
    elems.append(Spacer(1, 0.5 * cm))

    # KPI strip
    arb_color = GREEN if data.total_arbitrage_value >= 0 else RED
    kpi_val_style = ParagraphStyle(
        "_kpi_v",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=arb_color,
        leading=20,
    )
    conf_color = (
        GREEN if data.confidence_score >= 0.75
        else AMBER if data.confidence_score >= 0.50
        else RED
    )
    kpi_conf_style = ParagraphStyle(
        "_kpi_c",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=conf_color,
        leading=20,
    )

    kpi = Table(
        [
            [
                Paragraph("Total Arbitrage Value", s["h2"]),
                Paragraph("Model Confidence",      s["h2"]),
                Paragraph("Market",                s["h2"]),
            ],
            [
                Paragraph(_fmt_currency(data.total_arbitrage_value, data.currency), kpi_val_style),
                Paragraph(_fmt_pct(data.confidence_score),                          kpi_conf_style),
                Paragraph(data.market,                                              s["kpi_market"]),
            ],
        ],
        colWidths=[_W / 3, _W / 3, _W / 3],
    )
    kpi.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("BACKGROUND",    (0, 1), (-1, 1), LIGHT_GRAY),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, WHITE),
    ]))
    elems.append(kpi)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_key_findings(data: ReportData, s: dict) -> list:
    elems: list = [
        Paragraph("Key Findings", s["h1"]),
        _section_rule(),
    ]
    for i, f in enumerate(data.key_findings, 1):
        badge_color = _impact_color(f.impact)
        badge_style = ParagraphStyle(
            f"_badge_{i}",
            fontName="Helvetica-Bold",
            fontSize=7,
            textColor=WHITE,
            backColor=badge_color,
            leading=10,
        )
        row = Table(
            [
                [
                    Paragraph(f" {f.impact.upper()} ", badge_style),
                    Paragraph(f"{i}. {f.title}", s["finding_title"]),
                ],
                [
                    "",
                    Paragraph(f.detail, s["finding_detail"]),
                ],
            ],
            colWidths=[1.5 * cm, _W - 1.5 * cm],
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elems.append(KeepTogether([row, Spacer(1, 0.2 * cm)]))
    return elems


def _build_arbitrage(data: ReportData, s: dict) -> list:
    elems: list = [
        Paragraph("Arbitrage Insights", s["h1"]),
        _section_rule(),
        Paragraph(
            "Price-spread windows identified for battery dispatch arbitrage.",
            s["caption"],
        ),
    ]
    col_w = [3.5 * cm, 2.3 * cm, 2.8 * cm, 2.4 * cm, 5.0 * cm]
    headers = ["Time Window", "Direction", "Spread ($/MWh)", "Confidence", "Notes"]
    rows = [[Paragraph(h, s["th"]) for h in headers]]

    for ins in data.arbitrage_insights:
        dir_hex  = HEX_BLUE  if ins.direction.lower() == "charge" else HEX_GREEN
        conf_hex = _confidence_hex(ins.confidence)
        rows.append([
            Paragraph(ins.window, s["td"]),
            Paragraph(
                f'<font color="{dir_hex}"><b>{ins.direction.upper()}</b></font>',
                s["td"],
            ),
            Paragraph(f"${ins.spread_mwh:.2f}", s["td"]),
            Paragraph(
                f'<font color="{conf_hex}"><b>{_fmt_pct(ins.confidence)}</b></font>',
                s["td"],
            ),
            Paragraph(ins.notes or "—", s["td"]),
        ])

    tbl = Table(rows, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("ALIGN",         (2, 0), (3, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D8E4")),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_battery(data: ReportData, s: dict) -> list:
    elems: list = [
        Paragraph("Battery Recommendations", s["h1"]),
        _section_rule(),
    ]
    action_colors = {
        "charge":    ELECTRIC_BLUE,
        "discharge": GREEN,
        "hold":      AMBER,
    }
    for rec in data.battery_recommendations:
        ac = action_colors.get(rec.action.lower(), NAVY)
        head_style = ParagraphStyle(
            f"_rec_head_{rec.action}",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=WHITE,
            leading=14,
        )
        card = Table(
            [
                [Paragraph(
                    f"{rec.action.upper()}  |  {rec.time_window}",
                    head_style,
                )],
                [Paragraph(f"Target SoC: <b>{rec.soc_pct:.0f}%</b>", s["body"])],
                [Paragraph(rec.rationale, s["body"])],
            ],
            colWidths=[_W],
        )
        card.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), ac),
            ("BACKGROUND",    (0, 1), (-1, -1), LIGHT_GRAY),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 0.5, ac),
        ]))
        elems.append(KeepTogether([card, Spacer(1, 0.3 * cm)]))
    return elems


def _build_volatility(data: ReportData, s: dict) -> list:
    elems: list = [
        Paragraph("Volatility Analysis", s["h1"]),
        _section_rule(),
    ]
    col_w = [3.8 * cm, 2.4 * cm, 2.4 * cm, 2.0 * cm, 2.0 * cm, 2.4 * cm]
    headers = ["Period", "Mean ($/MWh)", "Std Dev", "Min", "Max", "Vol. Index"]
    rows = [[Paragraph(h, s["th"]) for h in headers]]

    for m in data.volatility_metrics:
        vi_hex = _vi_hex(m.volatility_index)
        rows.append([
            Paragraph(m.period, s["td"]),
            Paragraph(f"${m.mean_price:.2f}", s["td"]),
            Paragraph(f"${m.std_dev:.2f}",    s["td"]),
            Paragraph(f"${m.min_price:.2f}",  s["td"]),
            Paragraph(f"${m.max_price:.2f}",  s["td"]),
            Paragraph(
                f'<font color="{vi_hex}"><b>{m.volatility_index:.1f}</b></font>',
                s["td"],
            ),
        ])

    tbl = Table(rows, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D8E4")),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


# ── Markdown renderer ─────────────────────────────────────────────────────────

class _MarkdownRenderer:
    def render(self, data: ReportData) -> str:
        parts = [
            self._header(data),
            self._executive_summary(data),
            self._key_findings(data),
            self._arbitrage_insights(data),
            self._battery_recommendations(data),
            self._volatility_analysis(data),
            self._disclaimer(),
        ]
        return "\n\n---\n\n".join(parts)

    # ── sections ──────────────────────────────────────────────────────────────

    def _header(self, data: ReportData) -> str:
        subtitle = f"\n_{data.subtitle}_" if data.subtitle else ""
        return (
            f"# {data.title}{subtitle}\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| **Market** | {data.market} |\n"
            f"| **Period** | {data.date_range} |\n"
            f"| **Generated** | {data.generated_at.strftime('%Y-%m-%d %H:%M UTC')} |\n"
            f"| **Model Confidence** | {_fmt_pct(data.confidence_score)} |\n"
            f"| **Total Arbitrage Value** | {_fmt_currency(data.total_arbitrage_value, data.currency)} |"
        )

    def _executive_summary(self, data: ReportData) -> str:
        return f"## Executive Summary\n\n> {data.executive_summary}"

    def _key_findings(self, data: ReportData) -> str:
        lines = ["## Key Findings"]
        for i, f in enumerate(data.key_findings, 1):
            lines.append(
                f"\n### {i}. {f.title}  `{f.impact.upper()}`\n\n{f.detail}"
            )
        return "\n".join(lines)

    def _arbitrage_insights(self, data: ReportData) -> str:
        rows = [
            "## Arbitrage Insights",
            "",
            "| Time Window | Direction | Spread ($/MWh) | Confidence | Notes |",
            "|-------------|-----------|---------------|------------|-------|",
        ]
        for ins in data.arbitrage_insights:
            rows.append(
                f"| {ins.window} | **{ins.direction.upper()}** "
                f"| ${ins.spread_mwh:.2f} | {_fmt_pct(ins.confidence)} "
                f"| {ins.notes or '—'} |"
            )
        return "\n".join(rows)

    def _battery_recommendations(self, data: ReportData) -> str:
        sections = ["## Battery Recommendations"]
        for rec in data.battery_recommendations:
            sections.append(
                f"\n### {rec.action.upper()} — {rec.time_window}\n\n"
                f"**Target SoC:** {rec.soc_pct:.0f}%  \n"
                f"**Rationale:** {rec.rationale}"
            )
        return "\n".join(sections)

    def _volatility_analysis(self, data: ReportData) -> str:
        rows = [
            "## Volatility Analysis",
            "",
            "| Period | Mean ($/MWh) | Std Dev | Min | Max | Vol. Index |",
            "|--------|-------------|---------|-----|-----|-----------|",
        ]
        for m in data.volatility_metrics:
            rows.append(
                f"| {m.period} | ${m.mean_price:.2f} | ${m.std_dev:.2f} "
                f"| ${m.min_price:.2f} | ${m.max_price:.2f} | {m.volatility_index:.1f} |"
            )
        return "\n".join(rows)

    def _disclaimer(self) -> str:
        return (
            "*This report was generated automatically by GridMind-AI. "
            "All figures are model-derived estimates and must be independently "
            "validated before use in any trading or investment decision.*"
        )


# ── Main generator class ──────────────────────────────────────────────────────

class GridMindReportGenerator:
    """
    Generates investor-grade PDF and Markdown reports from ReportData.

    Usage:
        gen = GridMindReportGenerator()
        paths = gen.export(data)          # {"pdf": "...", "markdown": "..."}
        pdf_path = gen.generate_pdf(data)
        md_path  = gen.generate_markdown(data)
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._md = _MarkdownRenderer()

    # ── public API ────────────────────────────────────────────────────────────

    def generate_pdf(self, data: ReportData, filename: Optional[str] = None) -> str:
        """Build a PDF report and return the output file path."""
        path = self.output_dir / (filename or self._stem(data) + ".pdf")
        layout = _PageLayout(data.market)
        s = _styles()

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=2.5 * cm,
            rightMargin=2.5 * cm,
            topMargin=3.0 * cm,
            bottomMargin=2.5 * cm,
            title=data.title,
            author="GridMind-AI",
            subject=f"Energy Market Report — {data.market}",
        )

        story: list = []
        story += _build_cover(data, s)
        story += _build_executive_summary(data, s)
        story += _build_key_findings(data, s)
        story += _build_arbitrage(data, s)
        story += _build_battery(data, s)
        story += _build_volatility(data, s)

        doc.build(
            story,
            onFirstPage=layout.first_page,
            onLaterPages=layout.later_pages,
        )
        return str(path)

    def generate_markdown(self, data: ReportData, filename: Optional[str] = None) -> str:
        """Write a Markdown report and return the output file path."""
        path = self.output_dir / (filename or self._stem(data) + ".md")
        path.write_text(self._md.render(data), encoding="utf-8")
        return str(path)

    def export(
        self,
        data: ReportData,
        formats: Optional[list[str]] = None,
        filename_stem: Optional[str] = None,
    ) -> dict[str, str]:
        """Export to one or more formats. Returns {format: file_path}."""
        if formats is None:
            formats = ["pdf", "markdown"]
        stem = filename_stem or self._stem(data)
        results: dict[str, str] = {}
        for fmt in formats:
            if fmt == "pdf":
                results["pdf"]      = self.generate_pdf(data,      stem + ".pdf")
            elif fmt in ("markdown", "md"):
                results["markdown"] = self.generate_markdown(data, stem + ".md")
        return results

    # ── internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _stem(data: ReportData) -> str:
        slug = data.title.lower().replace(" ", "_")[:40]
        ts   = data.generated_at.strftime("%Y%m%d_%H%M")
        return f"{slug}_{ts}"


# ── Demo / CLI entrypoint ─────────────────────────────────────────────────────

def _demo_data() -> ReportData:
    return ReportData(
        title="ERCOT Energy Market — Weekly Analytical Report",
        subtitle="Battery Arbitrage & Price Volatility Assessment",
        market="ERCOT Day-Ahead",
        date_range="2026-05-10 – 2026-05-14",
        generated_at=datetime(2026, 5, 14, 9, 0, 0),
        confidence_score=0.83,
        total_arbitrage_value=142_650.00,
        currency="USD",
        executive_summary=(
            "During the week of May 10–14, 2026, ERCOT Day-Ahead prices exhibited elevated "
            "intra-day volatility driven by unexpected wind generation shortfalls and peak demand "
            "events on May 12–13. The GridMind-AI model identified five high-confidence arbitrage "
            "windows with a combined estimated value of USD 142,650. Off-peak charging windows in "
            "the early morning hours (02:00–06:00) offered average spreads of $38.40/MWh against "
            "afternoon peak discharge windows. Battery assets operating at optimal SoC targets "
            "are projected to capture approximately 87% of the available spread value."
        ),
        key_findings=[
            KeyFinding(
                title="Wind Generation Shortfall — May 12",
                detail=(
                    "Actual wind generation on May 12 fell 34% below day-ahead forecasts, "
                    "driving hub prices above $95/MWh during the 16:00–18:00 window. "
                    "Discharge-positioned assets captured an average spread of $52.10/MWh."
                ),
                impact="high",
            ),
            KeyFinding(
                title="Off-Peak Charging Opportunity — May 13–14",
                detail=(
                    "Overnight hours on May 13–14 presented sub-$30/MWh pricing windows "
                    "lasting 4–6 hours, enabling full recharge cycles ahead of the Friday "
                    "afternoon peak. Model confidence for this window is 91%."
                ),
                impact="medium",
            ),
            KeyFinding(
                title="Elevated Price Spike Risk — May 15 Outlook",
                detail=(
                    "Weekend load forecasts indicate a potential heat event on May 15 "
                    "with temperatures forecast at 96°F in Dallas. Volatility index is elevated "
                    "at 74.2. Battery assets should reach full charge by 08:00 Saturday."
                ),
                impact="high",
            ),
            KeyFinding(
                title="CPS Energy Interconnect Constraint",
                detail=(
                    "A 200 MW curtailment constraint on the CPS Energy interconnect on May 11 "
                    "introduced locational price basis risk. Minor impact on total captured "
                    "value (~$3,200 shortfall vs. model estimate)."
                ),
                impact="low",
            ),
        ],
        arbitrage_insights=[
            ArbitrageInsight(
                window="02:00–06:00 EST",
                spread_mwh=38.40,
                confidence=0.91,
                direction="charge",
                notes="Overnight valley; consistent 4-hour window",
            ),
            ArbitrageInsight(
                window="16:00–19:00 EST",
                spread_mwh=52.10,
                confidence=0.87,
                direction="discharge",
                notes="Peak demand + wind shortfall on May 12",
            ),
            ArbitrageInsight(
                window="11:00–13:00 EST",
                spread_mwh=21.30,
                confidence=0.74,
                direction="discharge",
                notes="Shoulder peak; moderate confidence",
            ),
            ArbitrageInsight(
                window="03:00–05:00 EST",
                spread_mwh=29.80,
                confidence=0.88,
                direction="charge",
                notes="May 13–14 overnight recharge window",
            ),
            ArbitrageInsight(
                window="07:00–09:00 EST",
                spread_mwh=18.50,
                confidence=0.62,
                direction="discharge",
                notes="Morning ramp; lower confidence due to solar uncertainty",
            ),
        ],
        battery_recommendations=[
            BatteryRecommendation(
                action="Charge",
                time_window="02:00–06:00 EST",
                soc_pct=95,
                rationale=(
                    "Overnight pricing consistently below $32/MWh provides optimal charging "
                    "economics. Target 95% SoC to maximise afternoon discharge capacity. "
                    "Grid frequency is stable during this window — no ramp risk."
                ),
            ),
            BatteryRecommendation(
                action="Discharge",
                time_window="16:00–19:00 EST",
                soc_pct=15,
                rationale=(
                    "Peak demand window with elevated wind-deficit risk. Deploy full capacity "
                    "during this window. Retain 15% SoC as operational reserve. "
                    "Expected revenue: $52.10/MWh × rated capacity."
                ),
            ),
            BatteryRecommendation(
                action="Hold",
                time_window="09:00–14:00 EST",
                soc_pct=80,
                rationale=(
                    "Mid-morning solar generation is suppressing prices below arbitrage threshold. "
                    "Maintain 80% SoC reserve. Avoid partial discharge that would compromise "
                    "afternoon peak positioning."
                ),
            ),
        ],
        volatility_metrics=[
            VolatilityMetrics("Mon May 10", 47.30, 12.80, 28.10,  81.50, 42.5),
            VolatilityMetrics("Tue May 11", 51.20, 18.40, 24.60,  94.30, 58.1),
            VolatilityMetrics("Wed May 12", 63.80, 28.90, 29.40, 124.70, 74.2),
            VolatilityMetrics("Thu May 13", 54.10, 21.30, 26.80, 103.20, 61.8),
            VolatilityMetrics("Fri May 14", 49.60, 14.70, 27.90,  88.40, 47.3),
        ],
    )


if __name__ == "__main__":
    gen   = GridMindReportGenerator(output_dir="reports")
    data  = _demo_data()
    paths = gen.export(data)
    for fmt, path in paths.items():
        print(f"[{fmt}] {path}")
