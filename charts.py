"""
Veridian — Charts
------------------
Generates all visual analytics for the DD report:
  1. Radar chart — market/team/product/traction/risk
  2. Score benchmark bars — vs deal history average
  3. Competitive positioning scatter — 2x2 matrix
  4. Risk heatmap — severity grid
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Design tokens (matches VC aesthetic) ─────────────────────────────────────
CREAM      = "#F7F4EE"
CREAM_DARK = "#EDE9E0"
INK        = "#1A1714"
INK_SOFT   = "#3D3830"
INK_MUTED  = "#8C8479"
INK_FAINT  = "#C4BFB6"
RUST       = "#B5541C"
BORDER     = "#E2DDD6"
WHITE      = "#FFFFFF"
INVEST     = "#3D6B4F"
WATCH      = "#8C6B1A"
PASS_COL   = "#8C2A2A"

FONT = "DM Sans, sans-serif"
MONO = "DM Mono, monospace"

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=WHITE,
    font=dict(family=FONT, color=INK_SOFT, size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)


def score_color(s):
    if s >= 7: return INVEST
    if s >= 5: return WATCH
    return PASS_COL


# ── 1. Radar Chart ────────────────────────────────────────────────────────────
def radar_chart(report: dict) -> go.Figure:
    sections = report.get("sections", {})
    categories = ["Market", "Team", "Product", "Traction", "Risk"]
    scores = [
        sections.get("market", {}).get("score", 0),
        sections.get("team", {}).get("score", 0),
        sections.get("product", {}).get("score", 0),
        sections.get("traction", {}).get("score", 0),
        # Risk is inverse — high risk = lower score
        10 - min(len(sections.get("risks", {}).get("top_risks", [])) * 2, 8),
    ]

    # Close the polygon
    cats_closed   = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()

    # Background reference rings
    for level in [2, 4, 6, 8, 10]:
        ring = [level] * (len(categories) + 1)
        fig.add_trace(go.Scatterpolar(
            r=ring, theta=cats_closed,
            fill="none",
            line=dict(color=BORDER, width=0.5),
            showlegend=False, hoverinfo="skip",
        ))

    # Main score area
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor="rgba(181,84,28,0.09)",
        line=dict(color=RUST, width=2),
        marker=dict(size=6, color=RUST),
        name=report.get("company_name", "Company"),
        hovertemplate="%{theta}: <b>%{r}/10</b><extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        polar=dict(
            bgcolor=WHITE,
            radialaxis=dict(
                visible=True, range=[0, 10],
                tickfont=dict(size=9, color=INK_FAINT, family=MONO),
                gridcolor=BORDER, linecolor=BORDER,
                tickvals=[0, 2, 4, 6, 8, 10],
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=INK_SOFT, family=FONT),
                gridcolor=BORDER, linecolor=BORDER,
            ),
        ),
        showlegend=False,
        height=320,
        title=dict(text="Score Profile", font=dict(size=11, color=INK_MUTED, family=MONO), x=0.5),
    )
    return fig


# ── 2. Benchmark Bars ─────────────────────────────────────────────────────────
def benchmark_bars(report: dict, history: list[dict] = None) -> go.Figure:
    """
    Compare this company's scores against deal history average.
    If no history, shows scores vs a market benchmark of 5.5.
    """
    sections = report.get("sections", {})
    labels   = ["Market", "Team", "Product", "Traction", "Overall"]
    scores   = [
        sections.get("market", {}).get("score", 0),
        sections.get("team", {}).get("score", 0),
        sections.get("product", {}).get("score", 0),
        sections.get("traction", {}).get("score", 0),
        report.get("overall_score", 0),
    ]

    # Compute averages from history or use benchmark
    if history and len(history) > 1:
        avgs = []
        for key in ["market_score", "team_score", "product_score", "traction_score", "overall_score"]:
            vals = [h.get(key, 0) for h in history if h.get(key)]
            avgs.append(round(sum(vals) / len(vals), 1) if vals else 5.5)
        benchmark_label = "Your deal avg"
    else:
        avgs = [5.5] * 5
        benchmark_label = "Market benchmark"

    colors = [score_color(s) for s in scores]

    fig = go.Figure()

    # Benchmark bars (behind)
    fig.add_trace(go.Bar(
        name=benchmark_label,
        x=labels, y=avgs,
        marker=dict(color=CREAM_DARK, line=dict(color=BORDER, width=1)),
        width=0.5,
        hovertemplate=f"{benchmark_label}: <b>%{{y}}/10</b><extra></extra>",
    ))

    # Company bars (front)
    fig.add_trace(go.Bar(
        name=report.get("company_name", "Company"),
        x=labels, y=scores,
        marker=dict(color=colors, opacity=0.85),
        width=0.3,
        hovertemplate="<b>%{x}</b>: %{y}/10<extra></extra>",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        barmode="overlay",
        height=280,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=10, color=INK_MUTED, family=MONO),
        ),
        xaxis=dict(
            tickfont=dict(size=10, color=INK_SOFT, family=FONT),
            gridcolor=CREAM_DARK, linecolor=BORDER, showgrid=False,
        ),
        yaxis=dict(
            range=[0, 10.5], gridcolor=CREAM_DARK, linecolor=BORDER,
            tickfont=dict(size=9, color=INK_FAINT, family=MONO),
            tickvals=[0, 2, 4, 6, 8, 10],
        ),
        title=dict(text="Score vs Benchmark", font=dict(size=11, color=INK_MUTED, family=MONO), x=0.5),
    )
    return fig


# ── 3. Competitive Positioning Scatter ────────────────────────────────────────
def competitive_scatter(report: dict, competitors: list[dict]) -> go.Figure:
    """
    2x2 scatter: Market Score (x) vs Threat Level (y).
    Main company + competitors plotted together.
    """
    if not competitors:
        return None

    threat_map = {"HIGH": 8.5, "MEDIUM": 5.5, "LOW": 2.5, "UNKNOWN": 4.0}

    fig = go.Figure()

    # Quadrant shading
    fig.add_shape(type="rect", x0=0, y0=5, x1=5, y1=10,
                  fillcolor="rgba(140,107,26,0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=5, y0=5, x1=10, y1=10,
                  fillcolor="rgba(140,42,42,0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=0, y0=0, x1=5, y1=5,
                  fillcolor=CREAM_DARK, line=dict(width=0), opacity=0.3)
    fig.add_shape(type="rect", x0=5, y0=0, x1=10, y1=5,
                  fillcolor="rgba(61,107,79,0.06)", line=dict(width=0))

    # Quadrant labels
    for x, y, text in [(2.5, 9, "WATCH"), (7.5, 9, "HIGH THREAT"),
                        (2.5, 1, "LOW PRIORITY"), (7.5, 1, "OPPORTUNITY")]:
        fig.add_annotation(x=x, y=y, text=text, showarrow=False,
                           font=dict(size=8, color=INK_FAINT, family=MONO))

    # Competitors
    for comp in competitors:
        threat_score = threat_map.get(comp.get("threat_level", "UNKNOWN"), 4.0)
        market_score = comp.get("market_score", 5)
        fig.add_trace(go.Scatter(
            x=[market_score], y=[threat_score],
            mode="markers+text",
            text=[comp.get("name", "")[:12]],
            textposition="top center",
            textfont=dict(size=9, color=INK_SOFT, family=FONT),
            marker=dict(size=12, color=CREAM_DARK,
                        line=dict(color=INK_FAINT, width=1.5)),
            name=comp.get("name", ""),
            hovertemplate=f"<b>{comp.get('name','')}</b><br>Market: %{{x}}/10<br>Threat: {comp.get('threat_level','')}<extra></extra>",
        ))

    # Main company (highlighted)
    main_score = report.get("overall_score", 5)
    fig.add_trace(go.Scatter(
        x=[main_score], y=[3.0],  # Low threat to itself
        mode="markers+text",
        text=[report.get("company_name", "")[:14]],
        textposition="top center",
        textfont=dict(size=10, color=RUST, family=FONT),
        marker=dict(size=18, color=RUST, symbol="diamond",
                    line=dict(color=WHITE, width=2)),
        name=report.get("company_name", ""),
        hovertemplate=f"<b>{report.get('company_name','')}</b><br>Score: {main_score}/10<extra></extra>",
    ))

    # Divider lines
    fig.add_hline(y=5, line_dash="dot", line_color=BORDER, line_width=1)
    fig.add_vline(x=5, line_dash="dot", line_color=BORDER, line_width=1)

    fig.update_layout(
        **BASE_LAYOUT,
        height=320,
        showlegend=False,
        xaxis=dict(
            range=[0, 10], title=dict(text="Market Score →", font=dict(size=10, color=INK_MUTED, family=MONO)),
            gridcolor=CREAM_DARK, linecolor=BORDER,
            tickfont=dict(size=9, color=INK_FAINT, family=MONO),
        ),
        yaxis=dict(
            range=[0, 10], title=dict(text="Competitive Threat →", font=dict(size=10, color=INK_MUTED, family=MONO)),
            gridcolor=CREAM_DARK, linecolor=BORDER,
            tickfont=dict(size=9, color=INK_FAINT, family=MONO),
        ),
        title=dict(text="Competitive Positioning", font=dict(size=11, color=INK_MUTED, family=MONO), x=0.5),
    )
    return fig


# ── 4. Risk Heatmap ───────────────────────────────────────────────────────────
def risk_heatmap(report: dict) -> go.Figure:
    """
    Grid of risk categories coloured by severity.
    Inferred from the report's risk section + scores.
    """
    sections = report.get("sections", {})
    risks    = sections.get("risks", {})
    market   = sections.get("market", {})
    team     = sections.get("team", {})
    product  = sections.get("product", {})
    traction = sections.get("traction", {})

    # Risk severity = inverse of score, scaled 1-10
    def risk_val(score): return max(1, 10 - score)

    # Build risk matrix
    categories = ["Market Risk", "Team Risk", "Product Risk", "Traction Risk",
                  "Competitive Risk", "Regulatory Risk"]
    dimensions = ["Likelihood", "Impact", "Mitigation"]

    # Infer values from report
    market_r  = risk_val(market.get("score", 5))
    team_r    = risk_val(team.get("score", 5))
    product_r = risk_val(product.get("score", 5))
    traction_r = risk_val(traction.get("score", 5))
    n_risks   = len(risks.get("top_risks", []))
    n_breaks  = len(risks.get("deal_breakers", []))
    n_mits    = len(risks.get("mitigants", []))

    competitive_r = min(5 + n_risks, 9)
    regulatory_r  = 4  # Default moderate — can't infer without more context

    mitigation_adjustment = max(1, 3 - n_mits)

    z = [
        # Likelihood
        [market_r, team_r, product_r, traction_r, competitive_r, regulatory_r],
        # Impact
        [min(market_r + 1, 10), min(team_r + 1, 10), product_r,
         min(traction_r + 1, 10), min(competitive_r + 1, 10), regulatory_r],
        # Mitigation (lower = better mitigated)
        [max(market_r - n_mits, 1), max(team_r - mitigation_adjustment, 1),
         max(product_r - 1, 1), max(traction_r - 1, 1),
         max(competitive_r - 1, 1), regulatory_r],
    ]

    # Custom colorscale — cream to rust
    colorscale = [
        [0.0,  CREAM_DARK],
        [0.3,  "#F5D5B8"],
        [0.6,  "#D4854A"],
        [0.85, RUST],
        [1.0,  "#7A2E0A"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=categories,
        y=dimensions,
        colorscale=colorscale,
        zmin=1, zmax=10,
        text=[[str(v) for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=11, family=MONO, color=WHITE),
        hovertemplate="<b>%{x}</b><br>%{y}: <b>%{z}/10</b><extra></extra>",
        showscale=True,
        colorbar=dict(
            thickness=8, len=0.8,
            tickfont=dict(size=8, color=INK_MUTED, family=MONO),
            tickvals=[1, 5, 10],
            ticktext=["Low", "Med", "High"],
        ),
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        height=220,
        xaxis=dict(
            tickfont=dict(size=9, color=INK_SOFT, family=FONT),
            side="bottom",
        ),
        yaxis=dict(
            tickfont=dict(size=9, color=INK_SOFT, family=MONO),
            autorange="reversed",
        ),
        title=dict(text="Risk Heatmap", font=dict(size=11, color=INK_MUTED, family=MONO), x=0.5),
    )
    return fig
