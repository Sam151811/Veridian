"""
Veridian — Due Diligence Copilot
Redesigned: centred layout, stronger logo, same VC editorial aesthetic
"""

import streamlit as st
import json, os, time, re
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def get_api_key() -> str:
    """Resolve Gemini API key from env, Streamlit secrets, or session state."""
    key = os.getenv("GEMINI_API_KEY", "")
    if key: return key
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key: return key
    except Exception:
        pass
    return st.session_state.get("user_api_key", "")


st.set_page_config(page_title="Veridian", page_icon="◈", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,200;0,9..144,300;0,9..144,400;1,9..144,200;1,9..144,300;1,9..144,400&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@300;400&display=swap');

:root {
    --cream: #F7F4EE; --cream-dark: #EDE9E0; --cream-mid: #E5E0D5;
    --ink: #1A1714; --ink-soft: #3D3830; --ink-muted: #8C8479; --ink-faint: #C4BFB6;
    --rust: #B5541C; --rust-light: #F5E8E0; --rust-mid: #D4622A;
    --border: #E2DDD6; --white: #FFFFFF;
    --invest: #3D6B4F; --invest-light: #E8F0EB;
    --watch: #8C6B1A; --watch-light: #F5EED8;
    --pass: #8C2A2A; --pass-light: #F5E0E0;
}

* { box-sizing: border-box; }
.stApp { background: var(--cream); color: var(--ink); font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 1rem 4rem; max-width: 860px !important; margin: 0 auto; }

/* ── Hero nav ── */
.v-hero {
    text-align: center;
    padding: 4rem 2rem 3rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 3rem;
}
.v-logo-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px; height: 52px;
    border: 1.5px solid var(--ink);
    margin: 0 auto 1.5rem;
    position: relative;
}
.v-logo-mark::before {
    content: '';
    position: absolute;
    width: 28px; height: 28px;
    border: 1px solid var(--rust);
    transform: rotate(45deg);
}
.v-logo-inner {
    width: 8px; height: 8px;
    background: var(--rust);
    border-radius: 50%;
    position: relative;
    z-index: 1;
}
.v-wordmark {
    font-family: 'Fraunces', serif;
    font-size: 2.8rem;
    font-weight: 200;
    letter-spacing: -0.04em;
    color: var(--ink);
    line-height: 1;
    margin-bottom: 0.5rem;
}
.v-wordmark em {
    font-style: italic;
    color: var(--rust);
}
.v-tagline {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    color: var(--ink-muted);
    text-transform: uppercase;
    margin-bottom: 0;
}

/* ── Input card ── */
.input-card {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
}

/* ── Section label ── */
.section-label {
    font-family: 'DM Mono', monospace; font-size: 0.58rem; letter-spacing: 0.2em;
    color: var(--ink-muted); text-transform: uppercase; margin-bottom: 1.25rem;
    display: flex; align-items: center; gap: 0.75rem;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── Verdict badge ── */
.verdict-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-family: 'DM Mono', monospace; font-size: 0.68rem;
    letter-spacing: 0.15em; text-transform: uppercase;
    padding: 0.4rem 1.1rem; border: 1px solid;
}
.verdict-invest { background: var(--invest-light); color: var(--invest); border-color: var(--invest); }
.verdict-watch  { background: var(--watch-light);  color: var(--watch);  border-color: var(--watch); }
.verdict-pass   { background: var(--pass-light);   color: var(--pass);   border-color: var(--pass); }

/* ── Report ── */
.report-eyebrow { font-family: 'DM Mono', monospace; font-size: 0.58rem; letter-spacing: 0.2em; color: var(--ink-muted); text-transform: uppercase; margin-bottom: 0.75rem; }
.report-company { font-family: 'Fraunces', serif; font-size: 2.6rem; font-weight: 200; color: var(--ink); letter-spacing: -0.03em; line-height: 1.05; margin: 0.5rem 0; }
.report-one-line { font-family: 'Fraunces', serif; font-size: 1.05rem; font-style: italic; color: var(--ink-muted); margin-bottom: 1rem; }
.report-tldr { font-family: 'DM Sans', sans-serif; font-size: 0.92rem; font-weight: 300; color: var(--ink-soft); line-height: 1.7; }

/* ── Score strip ── */
.score-strip { display: grid; border: 1px solid var(--border); margin: 2rem 0; }
.score-cell { padding: 1.25rem 1.5rem; border-right: 1px solid var(--border); background: var(--cream); }
.score-cell:last-child { border-right: none; }
.score-label { font-family: 'DM Mono', monospace; font-size: 0.55rem; letter-spacing: 0.18em; color: var(--ink-muted); text-transform: uppercase; margin-bottom: 0.5rem; }
.score-num { font-family: 'Fraunces', serif; font-size: 2rem; font-weight: 300; line-height: 1; letter-spacing: -0.02em; }
.score-num.high { color: var(--invest); }
.score-num.mid  { color: var(--watch); }
.score-num.low  { color: var(--pass); }
.score-bar { height: 2px; background: var(--border); margin-top: 0.4rem; }
.score-bar-fill { height: 2px; }

/* ── DD cards ── */
.dd-card { border: 1px solid var(--border); padding: 1.5rem; margin-bottom: 1rem; background: var(--cream); }
.dd-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--cream-dark); }
.dd-card-title { font-family: 'DM Mono', monospace; font-size: 0.58rem; letter-spacing: 0.15em; color: var(--ink-muted); text-transform: uppercase; }
.dd-card-score { font-family: 'Fraunces', serif; font-size: 1rem; font-weight: 300; }
.dd-text { font-family: 'DM Sans', sans-serif; font-size: 0.87rem; font-weight: 300; color: var(--ink-soft); line-height: 1.7; }
.dd-sublabel { font-family: 'DM Mono', monospace; font-size: 0.53rem; letter-spacing: 0.15em; color: var(--ink-faint); text-transform: uppercase; margin: 0.85rem 0 0.35rem; }
.dd-list { list-style: none; padding: 0; margin: 0; }
.dd-list li { font-family: 'DM Sans', sans-serif; font-size: 0.84rem; font-weight: 300; color: var(--ink-soft); padding: 0.25rem 0 0.25rem 1.25rem; position: relative; line-height: 1.55; }
.dd-list li::before { position: absolute; left: 0; font-size: 0.7rem; top: 0.3rem; }
.dd-list.arrow li::before { content: '→'; color: var(--ink-faint); }
.dd-list.risk li::before { content: '↑'; color: var(--watch); }
.dd-list.danger li::before { content: '✕'; color: var(--pass); }
.dd-list.good li::before { content: '✓'; color: var(--invest); }
.dd-list.question li::before { content: '?'; color: var(--rust); }

/* ── Competitor card ── */
.comp-card { border: 1px solid var(--border); padding: 1.25rem; background: var(--white); margin-bottom: 0.75rem; }
.comp-name { font-family: 'Fraunces', serif; font-size: 1.1rem; font-weight: 300; color: var(--ink); }
.comp-liner { font-family: 'DM Sans', sans-serif; font-size: 0.8rem; color: var(--ink-muted); font-weight: 300; margin: 0.25rem 0 0.75rem; }

/* ── Founder card ── */
.founder-card { border: 1px solid var(--border); border-left: 3px solid var(--invest); padding: 1.5rem; background: var(--invest-light); margin-bottom: 1.5rem; }

/* ── Recommendation ── */
.rec-box { border-left: 3px solid var(--rust); background: var(--rust-light); padding: 1.5rem; margin-top: 2rem; }
.rec-label { font-family: 'DM Mono', monospace; font-size: 0.55rem; letter-spacing: 0.2em; color: var(--rust); text-transform: uppercase; margin-bottom: 0.75rem; }
.rec-text { font-family: 'Fraunces', serif; font-size: 1.05rem; font-weight: 200; font-style: italic; color: var(--ink); line-height: 1.7; }

/* ── History ── */
.history-row { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border); }
.history-name { font-family: 'Fraunces', serif; font-size: 0.9rem; color: var(--ink-soft); }
.history-meta { font-family: 'DM Mono', monospace; font-size: 0.55rem; color: var(--ink-faint); margin-top: 0.1rem; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-title { font-family: 'Fraunces', serif; font-size: 1.6rem; font-weight: 200; font-style: italic; color: var(--ink-muted); margin-bottom: 0.5rem; }
.empty-sub { font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: var(--ink-faint); font-weight: 300; line-height: 1.6; }

/* ── Streamlit overrides ── */
.stTextInput > div > div > input {
    background: var(--white) !important; border: 1px solid var(--border) !important;
    border-radius: 0 !important; color: var(--ink) !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus { border-color: var(--rust) !important; box-shadow: none !important; }
.stTextArea > div > div > textarea {
    background: var(--white) !important; border: 1px solid var(--border) !important;
    border-radius: 0 !important; color: var(--ink) !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important;
}
.stFileUploader > div { background: var(--white) !important; border: 1px solid var(--border) !important; border-radius: 0 !important; }
.stButton > button {
    background: var(--ink) !important; color: var(--cream) !important;
    border: none !important; border-radius: 0 !important;
    font-family: 'DM Mono', monospace !important; font-size: 0.65rem !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    padding: 0.85rem 2rem !important; width: 100% !important; margin-top: 0.75rem !important;
}
.stButton > button:hover { background: var(--rust) !important; }
.stRadio > div { gap: 0.5rem !important; }
.stRadio label, .stCheckbox label { font-family: 'DM Sans', sans-serif !important; font-size: 0.87rem !important; color: var(--ink-soft) !important; }
div[data-testid="stTabs"] button { font-family: 'DM Mono', monospace !important; font-size: 0.6rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; border-radius: 0 !important; }
.stDownloadButton > button { background: var(--white) !important; color: var(--ink) !important; border: 1px solid var(--border) !important; border-radius: 0 !important; font-family: 'DM Mono', monospace !important; font-size: 0.62rem !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; margin-top: 0.5rem !important; width: auto !important; }
div[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 0 !important; background: var(--cream) !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def sc(s): return "high" if s>=7 else "mid" if s>=5 else "low"
def scol(s): return "var(--invest)" if s>=7 else "var(--watch)" if s>=5 else "var(--pass)"
def vcls(v): return {"INVEST":"invest","WATCH":"watch","PASS":"pass"}.get(v,"watch")
def vicon(v): return {"INVEST":"◆","WATCH":"◉","PASS":"✕"}.get(v,"◉")
def vcol(v): return {"INVEST":"var(--invest)","WATCH":"var(--watch)","PASS":"var(--pass)"}.get(v,"var(--watch)")


def render_report(report, signals=None, founder_data=None):
    company  = report.get("company_name","Unknown")
    verdict  = report.get("verdict","WATCH")
    conf     = report.get("confidence","MEDIUM")
    tldr     = report.get("tldr","")
    overall  = report.get("overall_score",5)
    one_line = report.get("one_line_verdict","")
    rec      = report.get("recommendation","")
    sections = report.get("sections",{})
    market   = sections.get("market",{})
    team     = sections.get("team",{})
    product  = sections.get("product",{})
    traction = sections.get("traction",{})
    risks    = sections.get("risks",{})
    comps    = sections.get("comparables",{})
    qs       = sections.get("questions_to_ask",[])

    # Header
    st.markdown(f"""
    <div style="padding-bottom:2.5rem;margin-bottom:2rem;border-bottom:1px solid var(--border)">
        <div class="report-eyebrow">Due Diligence Report · {datetime.now().strftime('%d %b %Y')}</div>
        <div class="report-company">{company}</div>
        <div class="report-one-line">"{one_line}"</div>
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem">
            <span class="verdict-badge verdict-{vcls(verdict)}">{vicon(verdict)} {verdict}</span>
            <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:var(--ink-faint);letter-spacing:0.1em">CONFIDENCE: {conf}</span>
        </div>
        <div class="report-tldr">{tldr}</div>
    </div>""", unsafe_allow_html=True)

    # Scores
    scores = [("Market",market.get("score",0)),("Team",team.get("score",0)),
               ("Product",product.get("score",0)),("Traction",traction.get("score",0)),("Overall",overall)]
    cells = "".join(f"""<div class="score-cell">
        <div class="score-label">{l}</div>
        <div class="score-num {sc(s)}">{s}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:{int(s/10*100)}%;background:{scol(s)}"></div></div>
    </div>""" for l,s in scores)
    st.markdown(f'<div class="score-strip" style="grid-template-columns:repeat({len(scores)},1fr)">{cells}</div>', unsafe_allow_html=True)

    # ── Visual Analytics ─────────────────────────────────────────────
    try:
        from src.charts import radar_chart, benchmark_bars, risk_heatmap, competitive_scatter

        st.markdown('<div class="section-label" style="margin-top:0.5rem">Visual Analytics</div>', unsafe_allow_html=True)

        # Row 1: Radar + Benchmark
        ch1, ch2 = st.columns(2, gap="medium")
        with ch1:
            fig_radar = radar_chart(report)
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
        with ch2:
            try:
                from src.database import fetch_reports
                history = fetch_reports(limit=20)
            except Exception:
                history = []
            fig_bench = benchmark_bars(report, history)
            st.plotly_chart(fig_bench, use_container_width=True, config={"displayModeBar": False})

        # Row 2: Risk heatmap full width
        fig_heat = risk_heatmap(report)
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

        # Row 3: Competitive scatter (only if competitors available)
        competitors = st.session_state.get("current_report", {}).get("competitors", [])
        if competitors:
            fig_scatter = competitive_scatter(report, competitors)
            if fig_scatter:
                st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

    except Exception as e:
        st.warning(f"Charts unavailable: {e}")

    # Founder card
    if founder_data and founder_data.get("success"):
        fa = founder_data.get("analysis",{})
        fit = fa.get("founder_market_fit_score",0)
        gf = "".join(f"<li>{g}</li>" for g in fa.get("green_flags",[]))
        rf = "".join(f"<li>{r}</li>" for r in fa.get("red_flags",[]))
        st.markdown(f"""<div class="founder-card">
            <div class="dd-card-header">
                <div class="dd-card-title">◆ Founder Intelligence</div>
                <div class="dd-card-score" style="color:{scol(fit)}">{fit}/10 fit</div>
            </div>
            <div class="dd-text"><strong>{fa.get('name','')}</strong> — {fa.get('background_summary','')}</div>
            <div style="display:flex;gap:2rem;margin-top:1rem">
                <div><div class="dd-sublabel">Domain Expertise</div><div class="dd-text">{fa.get('domain_expertise','—')}</div></div>
                <div><div class="dd-sublabel">Prior Founder</div><div class="dd-text">{'Yes' if fa.get('prior_founder_experience') else 'No'}</div></div>
            </div>
            <div class="dd-sublabel">Fit Reasoning</div>
            <div class="dd-text">{fa.get('founder_market_fit_reasoning','')}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:0.75rem">
                <div><div class="dd-sublabel">Green Flags</div><ul class="dd-list good">{gf or '<li>None</li>'}</ul></div>
                <div><div class="dd-sublabel">Red Flags</div><ul class="dd-list risk">{rf or '<li>None</li>'}</ul></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # DD sections — two columns
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Market Opportunity</div><div class="dd-card-score" style="color:{scol(market.get('score',0))}">{market.get('score','—')}/10</div></div>
            <div class="dd-text">{market.get('summary','')}</div>
            <div class="dd-sublabel">Size</div><div class="dd-text">{market.get('size_estimate','')}</div>
            <div class="dd-sublabel">Timing</div><div class="dd-text">{market.get('timing','')}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Product & Differentiation</div><div class="dd-card-score" style="color:{scol(product.get('score',0))}">{product.get('score','—')}/10</div></div>
            <div class="dd-text">{product.get('summary','')}</div>
            <div class="dd-sublabel">Differentiation</div><div class="dd-text">{product.get('differentiation','')}</div>
            <div class="dd-sublabel">Moat</div><div class="dd-text">{product.get('moat','')}</div>
        </div>""", unsafe_allow_html=True)

        sim_h = "".join(f"<li>{c}</li>" for c in comps.get("similar_companies",[]))
        ex_h  = "".join(f"<li>{e}</li>" for e in comps.get("relevant_exits",[]))
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Comparables & Exits</div></div>
            <div class="dd-sublabel">Similar Companies</div><ul class="dd-list arrow">{sim_h or '<li>None identified</li>'}</ul>
            <div class="dd-sublabel">Relevant Exits</div><ul class="dd-list arrow">{ex_h or '<li>None identified</li>'}</ul>
            <div class="dd-sublabel">Valuation Anchor</div><div class="dd-text">{comps.get('valuation_anchor','')}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        fl_h = "".join(f"<li>{f}</li>" for f in team.get("red_flags",[]))
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Team & Founder Fit</div><div class="dd-card-score" style="color:{scol(team.get('score',0))}">{team.get('score','—')}/10</div></div>
            <div class="dd-text">{team.get('summary','')}</div>
            <div class="dd-sublabel">Founder-Market Fit</div><div class="dd-text">{team.get('founder_market_fit','')}</div>
            <div class="dd-sublabel">Red Flags</div><ul class="dd-list risk">{fl_h or '<li>None identified</li>'}</ul>
        </div>""", unsafe_allow_html=True)

        sg_h = "".join(f"<li>{s}</li>" for s in traction.get("signals",[]))
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Traction Signals</div><div class="dd-card-score" style="color:{scol(traction.get('score',0))}">{traction.get('score','—')}/10</div></div>
            <div class="dd-text">{traction.get('summary','')}</div>
            <div class="dd-sublabel">Evidence</div><ul class="dd-list good">{sg_h or '<li>None identified</li>'}</ul>
            <div class="dd-sublabel">Real vs Claimed</div><div class="dd-text">{traction.get('what_is_real_vs_claimed','')}</div>
        </div>""", unsafe_allow_html=True)

        rk_h  = "".join(f"<li>{r}</li>" for r in risks.get("top_risks",[]))
        mt_h  = "".join(f"<li>{m}</li>" for m in risks.get("mitigants",[]))
        db_h  = "".join(f"<li>{d}</li>" for d in risks.get("deal_breakers",[]))
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Risk Assessment</div></div>
            <div class="dd-sublabel">Top Risks</div><ul class="dd-list risk">{rk_h or '<li>None</li>'}</ul>
            <div class="dd-sublabel">Mitigants</div><ul class="dd-list good">{mt_h or '<li>None</li>'}</ul>
            <div class="dd-sublabel">Deal Breakers</div><ul class="dd-list danger">{db_h or '<li>None</li>'}</ul>
        </div>""", unsafe_allow_html=True)

    if qs:
        q_h = "".join(f"<li>{q}</li>" for q in qs)
        st.markdown(f"""<div class="dd-card">
            <div class="dd-card-header"><div class="dd-card-title">Questions to Ask the Founder</div></div>
            <ul class="dd-list question">{q_h}</ul>
        </div>""", unsafe_allow_html=True)

    # Competitor map
    if "competitors" in st.session_state.get("current_report",{}):
        competitors = st.session_state["current_report"]["competitors"]
        if competitors:
            st.markdown('<div class="section-label" style="margin-top:2rem">Competitor Landscape</div>', unsafe_allow_html=True)
            cc = st.columns(min(len(competitors),3))
            for i, comp in enumerate(competitors):
                threat = comp.get("threat_level","UNKNOWN")
                tcol = {"HIGH":"var(--pass)","MEDIUM":"var(--watch)","LOW":"var(--invest)"}.get(threat,"var(--ink-muted)")
                strengths = "".join(f"<li>{s}</li>" for s in comp.get("strengths",[]))
                with cc[i % len(cc)]:
                    st.markdown(f"""<div class="comp-card">
                        <div class="comp-name">{comp.get('name','')}</div>
                        <div class="comp-liner">{comp.get('one_liner','')}</div>
                        <div style="display:flex;gap:1rem;margin-bottom:0.75rem">
                            <div><div class="dd-sublabel">Stage</div><div class="dd-text">{comp.get('stage','—')}</div></div>
                            <div><div class="dd-sublabel">Threat</div><div class="dd-text" style="color:{tcol}">{threat}</div></div>
                        </div>
                        <div class="dd-sublabel">Strengths</div><ul class="dd-list arrow">{strengths or '<li>—</li>'}</ul>
                        <div class="dd-sublabel">vs {company}</div><div class="dd-text">{comp.get('vs_main','')}</div>
                    </div>""", unsafe_allow_html=True)

    # Recommendation
    st.markdown(f"""<div class="rec-box">
        <div class="rec-label">◆ Veridian Recommendation</div>
        <div class="rec-text">{rec}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="margin-top:2rem;font-family:\'DM Mono\',monospace;font-size:0.55rem;color:var(--ink-faint);letter-spacing:0.1em;text-align:center">VERIDIAN · AI DUE DILIGENCE · {datetime.now().strftime("%d %b %Y %H:%M")}</div>', unsafe_allow_html=True)


# ── Page ──────────────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="v-hero">
    <div class="v-logo-mark"><div class="v-logo-inner"></div></div>
    <div class="v-wordmark">Verid<em>ian</em></div>
    <div class="v-tagline">AI Due Diligence Copilot</div>
</div>""", unsafe_allow_html=True)

# Session state
for k, v in [("history", []), ("current_report", None), ("batch_results", None), ("user_api_key", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# API key check — show input if no key found
if not get_api_key():
    st.markdown("""
    <div style="background:var(--white);border:1px solid var(--border);border-left:3px solid var(--rust);padding:1.5rem 2rem;margin-bottom:2rem;text-align:center">
        <div style="font-family:'DM Mono',monospace;font-size:0.6rem;letter-spacing:0.2em;color:var(--rust);text-transform:uppercase;margin-bottom:0.5rem">API Key Required</div>
        <div style="font-family:'DM Sans',sans-serif;font-size:0.85rem;color:var(--ink-muted);font-weight:300;margin-bottom:1.25rem">
            Veridian uses Google Gemini AI — completely free, no credit card needed.
        </div>
        <div style="text-align:left;background:var(--cream);border:1px solid var(--border);padding:1.25rem 1.5rem;margin-bottom:1rem">
            <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:0.15em;color:var(--ink-muted);text-transform:uppercase;margin-bottom:0.75rem">How to get your free key — 2 minutes</div>
            <div style="font-family:'DM Sans',sans-serif;font-size:0.84rem;color:var(--ink-soft);font-weight:300;line-height:1.8">
                1. Go to <a href="https://aistudio.google.com" target="_blank" style="color:var(--rust);text-decoration:none">aistudio.google.com</a><br/>
                2. Sign in with any Google account<br/>
                3. Click <strong>Get API key</strong> → <strong>Create API key</strong><br/>
                4. Copy the key (starts with <span style="font-family:'DM Mono',monospace;font-size:0.8rem">AIza...</span>) and paste below
            </div>
        </div>
        <div style="font-family:'DM Sans',sans-serif;font-size:0.75rem;color:var(--ink-faint);font-weight:300">
            Free tier: 1,500 requests/day · No credit card · Key stays in your browser session only
        </div>
    </div>
    """, unsafe_allow_html=True)
    key_input = st.text_input("Gemini API Key", type="password",
                               placeholder="AIza...",
                               label_visibility="collapsed")
    if key_input:
        st.session_state.user_api_key = key_input
        os.environ["GEMINI_API_KEY"] = key_input
        st.rerun()
    st.stop()



# Mode tabs
tab1, tab2, tab3 = st.tabs(["Single Analysis", "Batch Mode", "History"])

# ════ TAB 1 ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Analyse a company</div>', unsafe_allow_html=True)

    input_type = st.radio("Input", ["Company URL", "Pitch Deck PDF"], horizontal=True, label_visibility="collapsed")

    url_input, pdf_input = "", None
    if input_type == "Company URL":
        url_input = st.text_input("URL", placeholder="https://stripe.com", label_visibility="collapsed")
    else:
        pdf_input = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

    c1, c2 = st.columns(2)
    with c1:
        linkedin_url = st.text_input("Founder LinkedIn (optional)", placeholder="https://linkedin.com/in/founder", label_visibility="visible")
    with c2:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    opt1, opt2 = st.columns(2)
    with opt1:
        enrich_signals = st.checkbox("Public signals", value=True)
    with opt2:
        map_competitors = st.checkbox("Map competitors", value=True)

    run_single = st.button("◈ Run Due Diligence")
    st.markdown('</div>', unsafe_allow_html=True)

    if run_single:
        has_input = (input_type == "Company URL" and url_input) or (input_type == "Pitch Deck PDF" and pdf_input)
        if not has_input:
            st.error("Please provide a URL or upload a PDF.")
        elif not get_api_key():
            st.error("GEMINI_API_KEY not found")
        else:
            with st.spinner("Analysing..."):
                from src.ingest import scrape_url, read_pdf, extract_company_name
                from src.enricher import enrich as enrich_fn
                from src.analyst import analyse
                from src.competitor import map_competitors as map_comps
                from src.linkedin import enrich_founder
                from src.database import save_report

                step = st.empty()
                def upd(msg): step.markdown(f'<div style="font-family:\'DM Mono\',monospace;font-size:0.68rem;color:var(--ink-muted);text-align:center;padding:0.5rem">{msg}</div>', unsafe_allow_html=True)

                upd("01 · Ingesting company data...")
                if input_type == "Company URL":
                    ingested = scrape_url(url_input)
                    domain = url_input.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
                else:
                    ingested = read_pdf(pdf_input); domain = ""

                if not ingested["success"]:
                    st.error(f"Ingest failed: {ingested.get('error','Unknown error')}")
                    st.stop()

                company_name = extract_company_name(ingested["text"], url_input)
                signals_text = ""
                if enrich_signals:
                    upd("02 · Pulling public signals...")
                    signals = enrich_fn(company_name, domain)
                    signals_text = signals.get("summary","")

                upd("03 · Running AI analysis...")
                result = analyse(ingested["text"], signals_text, company_name)
                step.empty()

                if not result["success"]:
                    st.error(f"Analysis failed: {result.get('error')}")
                    st.stop()

                report = result["report"]
                current = {"report": report}

                if linkedin_url:
                    upd("04 · Enriching founder profile...")
                    current["founder"] = enrich_founder(linkedin_url, company_name, ingested["text"][:400])

                if map_competitors:
                    upd("05 · Mapping competitors...")
                    current["competitors"] = map_comps(company_name, ingested["text"][:400], n=3)

                save_report(report, source_url=url_input, source_type=ingested.get("type","url"))
                st.session_state.current_report = current
                st.session_state.history.append({"company": report.get("company_name", company_name), "verdict": report.get("verdict","—"), "date": datetime.now().strftime("%d %b %Y")})
                st.rerun()

    if st.session_state.current_report:
        r = st.session_state.current_report
        render_report(r["report"], founder_data=r.get("founder"))
        # Download buttons
        dc1, dc2 = st.columns(2)
        with dc1:
            st.download_button("↓ Download Report (JSON)",
                data=json.dumps(r["report"], indent=2),
                file_name=f"veridian_{r['report'].get('company_name','report').lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json")
        with dc2:
            try:
                from src.pdf_export import generate_pdf
                rubric = st.session_state.get("rubric_weights")
                pdf_bytes = generate_pdf(r["report"], rubric_weights=rubric)
                st.download_button("↓ Download Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"veridian_{r['report'].get('company_name','report').lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf")
            except Exception as e:
                st.caption(f"PDF unavailable: install reportlab")

        # ── Follow-up Mode ────────────────────────────────────────────
        st.markdown('<div class="section-label" style="margin-top:2rem">Follow-up Mode</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family:\'DM Sans\',sans-serif;font-size:0.83rem;color:var(--ink-muted);font-weight:300;margin-bottom:0.75rem">Paste the founder\'s answers to Veridian\'s questions. Scores will be updated based on their responses.</p>', unsafe_allow_html=True)

        founder_answers = st.text_area(
            "Founder answers",
            placeholder="Paste the founder's answers here...\n\nYou can copy the questions from the report above and paste their responses alongside each one.",
            height=180,
            label_visibility="collapsed",
        )
        run_followup_btn = st.button("◈ Re-score with Founder Answers")

        if run_followup_btn and founder_answers.strip():
            with st.spinner("Re-scoring..."):
                from src.followup import run_followup
                result_fu = run_followup(r["report"], founder_answers)

            if result_fu["success"]:
                fu = result_fu["followup"]
                deltas = fu.get("score_deltas", {})
                updated = fu.get("updated_scores", {})
                verdict_changed = fu.get("verdict_changed", False)
                new_verdict = fu.get("updated_verdict", r["report"].get("verdict"))
                aq = fu.get("answer_quality", "ADEQUATE")
                aq_color = {"STRONG": "var(--invest)", "ADEQUATE": "var(--ink-muted)", "WEAK": "var(--watch)", "EVASIVE": "var(--pass)"}.get(aq, "var(--ink-muted)")

                st.markdown(f"""
                <div style="border:1px solid var(--border);background:var(--cream);padding:1.5rem;margin-top:1rem">
                    <div class="section-label">Follow-up Assessment</div>
                    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
                        <span style="font-family:'DM Mono',monospace;font-size:0.7rem;color:{aq_color};letter-spacing:0.1em">ANSWER QUALITY: {aq}</span>
                        {'<span class="verdict-badge verdict-' + vcls(new_verdict) + '">' + vicon(new_verdict) + ' VERDICT CHANGED → ' + new_verdict + '</span>' if verdict_changed else ''}
                    </div>
                    <div class="dd-text">{fu.get('answer_quality_reasoning','')}</div>
                </div>""", unsafe_allow_html=True)

                # Score deltas
                delta_cols = st.columns(5)
                for i, (label, key) in enumerate([("Market","market"),("Team","team"),("Product","product"),("Traction","traction"),("Overall","overall")]):
                    delta = deltas.get(key, 0)
                    new_s = updated.get(key, 0)
                    delta_str = f"+{delta}" if delta > 0 else str(delta)
                    delta_col = "var(--invest)" if delta > 0 else "var(--pass)" if delta < 0 else "var(--ink-faint)"
                    with delta_cols[i]:
                        st.markdown(f"""<div style="text-align:center;border:1px solid var(--border);padding:0.75rem;background:var(--cream)">
                            <div class="score-label">{label}</div>
                            <div class="score-num {sc(new_s)}">{new_s}</div>
                            <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:{delta_col}">{delta_str}</div>
                        </div>""", unsafe_allow_html=True)

                # Key insights + remaining concerns
                ki_html = "".join(f"<li>{i}</li>" for i in fu.get("key_insights",[]))
                rc_html = "".join(f"<li>{c}</li>" for c in fu.get("remaining_concerns",[]))
                nq_html = "".join(f"<li>{q}</li>" for q in fu.get("new_questions",[]))

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"""<div class="dd-card">
                        <div class="dd-card-header"><div class="dd-card-title">Key Insights from Answers</div></div>
                        <ul class="dd-list good">{ki_html or '<li>None</li>'}</ul>
                    </div>""", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"""<div class="dd-card">
                        <div class="dd-card-header"><div class="dd-card-title">Remaining Concerns</div></div>
                        <ul class="dd-list risk">{rc_html or '<li>None</li>'}</ul>
                        <div class="dd-sublabel">New Questions Raised</div>
                        <ul class="dd-list question">{nq_html or '<li>None</li>'}</ul>
                    </div>""", unsafe_allow_html=True)

                st.markdown(f"""<div class="rec-box">
                    <div class="rec-label">◆ Updated Recommendation</div>
                    <div class="rec-text">{fu.get('updated_recommendation','')}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.error(f"Follow-up failed: {result_fu.get('error')}")

        # ── Scoring Rubric ────────────────────────────────────────────
        with st.expander("⚙ Customise Scoring Rubric"):
            st.markdown('<p style="font-family:\'DM Sans\',sans-serif;font-size:0.83rem;color:var(--ink-muted);font-weight:300;margin-bottom:1rem">Adjust how much each dimension affects the overall score. Weights auto-normalise to 100%.</p>', unsafe_allow_html=True)

            if "rubric_weights" not in st.session_state:
                st.session_state.rubric_weights = {"market": 0.25, "team": 0.25, "product": 0.25, "traction": 0.25}

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                w_market = st.slider("Market", 0, 100, 25, label_visibility="visible")
            with rc2:
                w_team = st.slider("Team", 0, 100, 25, label_visibility="visible")
            with rc3:
                w_product = st.slider("Product", 0, 100, 25, label_visibility="visible")
            with rc4:
                w_traction = st.slider("Traction", 0, 100, 25, label_visibility="visible")

            total = w_market + w_team + w_product + w_traction
            if total > 0:
                weights = {
                    "market":   round(w_market / total, 3),
                    "team":     round(w_team / total, 3),
                    "product":  round(w_product / total, 3),
                    "traction": round(w_traction / total, 3),
                }
                st.session_state.rubric_weights = weights

                # Recompute weighted overall score
                sections = r["report"].get("sections", {})
                weighted_score = round(
                    weights["market"]   * sections.get("market", {}).get("score", 0) +
                    weights["team"]     * sections.get("team", {}).get("score", 0) +
                    weights["product"]  * sections.get("product", {}).get("score", 0) +
                    weights["traction"] * sections.get("traction", {}).get("score", 0),
                    1
                )

                st.markdown(f"""<div style="background:var(--cream-dark);border:1px solid var(--border);padding:1rem;margin-top:0.75rem;display:flex;justify-content:space-between;align-items:center">
                    <span style="font-family:'DM Mono',monospace;font-size:0.62rem;color:var(--ink-muted);letter-spacing:0.1em">WEIGHTED SCORE WITH YOUR RUBRIC</span>
                    <span style="font-family:'Fraunces',serif;font-size:1.8rem;font-weight:300;color:{scol(weighted_score)}">{weighted_score}/10</span>
                </div>""", unsafe_allow_html=True)

    elif not run_single:
        st.markdown("""<div class="empty-state">
            <div style="font-family:'Fraunces',serif;font-size:2.5rem;font-weight:200;color:var(--ink-faint);margin-bottom:1.5rem">◈</div>
            <div class="empty-title">Ready to analyse</div>
            <div class="empty-sub">Enter a URL or upload a pitch deck above<br/>to generate your due diligence report</div>
        </div>""", unsafe_allow_html=True)

# ════ TAB 2 ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Batch analyse a pipeline</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:\'DM Sans\',sans-serif;font-size:0.83rem;color:var(--ink-muted);font-weight:300;margin-bottom:0.75rem">One URL per line</p>', unsafe_allow_html=True)
    batch_text = st.text_area("URLs", placeholder="https://stripe.com\nhttps://notion.so\nhttps://linear.app", height=150, label_visibility="collapsed")
    batch_name = st.text_input("Run name (optional)", placeholder="Q2 2025 Pipeline", label_visibility="visible")
    run_batch_btn = st.button("◈ Run Batch Analysis")
    st.markdown('</div>', unsafe_allow_html=True)

    if run_batch_btn:
        urls = [u.strip() for u in batch_text.strip().split("\n") if u.strip()]
        if not urls:
            st.error("Please enter at least one URL.")
        elif not get_api_key():
            st.error("GEMINI_API_KEY not found")
        else:
            from src.batch import run_batch, to_dataframe
            from src.database import save_batch

            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, url in enumerate(urls):
                status.markdown(f'<div style="font-family:\'DM Mono\',monospace;font-size:0.68rem;color:var(--ink-muted);text-align:center">{i+1}/{len(urls)} · {url}</div>', unsafe_allow_html=True)
                batch_result = run_batch([{"url": url, "name": ""}], enrich=False, delay=1.0)
                results.extend(batch_result)
                progress.progress((i+1)/len(urls))

            progress.empty(); status.empty()
            save_batch(batch_name or "Untitled batch", urls, results)
            st.session_state.batch_results = results
            st.rerun()

    if st.session_state.batch_results:
        from src.batch import to_dataframe
        results = st.session_state.batch_results
        df = to_dataframe(results)

        st.markdown('<div class="section-label" style="margin-top:1.5rem">Results — ranked by verdict & score</div>', unsafe_allow_html=True)
        if not df.empty:
            display = df.drop(columns=[c for c in ["_url"] if c in df.columns])
            st.dataframe(display, use_container_width=True)

        st.markdown('<div class="section-label" style="margin-top:2rem">Individual Reports</div>', unsafe_allow_html=True)
        for r in results:
            if r.get("success") and r.get("report"):
                v = r.get("verdict","—")
                with st.expander(f"{vicon(v)} {r.get('name','')} — {v}"):
                    render_report(r["report"])

        st.download_button("↓ Download All (JSON)",
            data=json.dumps([r.get("report") for r in results if r.get("report")], indent=2),
            file_name=f"veridian_batch_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json")

# ════ TAB 3 ══════════════════════════════════════════════════════════════════
with tab3:
    saved = []
    try:
        from src.database import fetch_reports
        saved = fetch_reports(limit=30)
    except Exception:
        pass

    items = saved or st.session_state.history
    if items:
        st.markdown('<div class="section-label">Report History</div>', unsafe_allow_html=True)
        for item in (items if saved else list(reversed(items))):
            name    = item.get("company_name") or item.get("company","Unknown")
            verdict = item.get("verdict","—")
            date    = (item.get("created_at","")[:10] if saved else item.get("date",""))
            score   = item.get("overall_score","")
            st.markdown(f"""<div class="history-row">
                <div>
                    <div class="history-name">{name}</div>
                    <div class="history-meta">{date}{f' · Score {score}/10' if score else ''}</div>
                </div>
                <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:{vcol(verdict)}">{vicon(verdict)} {verdict}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="empty-state">
            <div class="empty-title">No reports yet</div>
            <div class="empty-sub">Your analysed companies will appear here</div>
        </div>""", unsafe_allow_html=True)
