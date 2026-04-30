# ◈ Veridian
### AI Due Diligence Copilot for Venture Investors

Paste a company URL or upload a pitch deck → get a structured DD report in 30 seconds.

## Setup

```bash
# 1. Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Add your Gemini API key
cp .env.example .env
# Edit .env and add your key from aistudio.google.com

# 3. Run
streamlit run app.py
```

## What Veridian analyses

- **Market** — size, timing, growth trajectory
- **Team** — founder-market fit, red flags
- **Product** — differentiation, moat
- **Traction** — real signals vs claimed metrics
- **Risks** — top risks, mitigants, deal breakers
- **Comparables** — similar companies, relevant exits
- **Questions** — what to ask the founder in a call

## Verdict system
- **◆ INVEST** — strong signal, move forward
- **◉ WATCH** — interesting but needs more data
- **✕ PASS** — clear concerns outweigh opportunity

## Tech stack
- Gemini 1.5 Flash (free tier — 1,500 req/day)
- Streamlit frontend
- BeautifulSoup for URL scraping
- pypdf for pitch deck parsing
- HackerNews + GitHub public APIs for signal enrichment
