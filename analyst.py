"""
Veridian — Analyst
-------------------
The brain. Sends company context to Gemini and gets back
a structured due diligence report.
"""

import os
import json
import re
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

DD_PROMPT = """You are Veridian, an expert venture capital analyst with 15 years of experience at top-tier VC firms. Your job is to produce rigorous, honest due diligence reports that help investors make better decisions.

You have been given:
1. Company information (scraped from their website or pitch deck)
2. Public signal data (HackerNews mentions, GitHub activity, news)

Produce a structured due diligence report in the following JSON format ONLY. No preamble, no markdown, just valid JSON:

{{
  "company_name": "string",
  "one_line_verdict": "string — one punchy sentence summarising your view",
  "verdict": "INVEST" | "WATCH" | "PASS",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "tldr": "string — 2-3 sentence executive summary",
  "sections": {{
    "market": {{
      "summary": "string",
      "size_estimate": "string",
      "timing": "string — is now the right time?",
      "score": 1-10
    }},
    "team": {{
      "summary": "string",
      "founder_market_fit": "string",
      "red_flags": ["string"],
      "score": 1-10
    }},
    "product": {{
      "summary": "string",
      "differentiation": "string",
      "moat": "string",
      "score": 1-10
    }},
    "traction": {{
      "summary": "string",
      "signals": ["string"],
      "what_is_real_vs_claimed": "string",
      "score": 1-10
    }},
    "risks": {{
      "top_risks": ["string"],
      "mitigants": ["string"],
      "deal_breakers": ["string"]
    }},
    "comparables": {{
      "similar_companies": ["string"],
      "relevant_exits": ["string"],
      "valuation_anchor": "string"
    }},
    "questions_to_ask": ["string — specific questions to ask the founder in a call"]
  }},
  "overall_score": 1-10,
  "recommendation": "string — 2-3 sentences on what you would do and why"
}}

Be honest and critical. VCs need to know what's wrong, not just what's right. If information is missing or unclear, say so explicitly. Do not hallucinate metrics or facts not present in the provided context.

---

COMPANY CONTEXT:
{company_text}

---

PUBLIC SIGNALS:
{signals_text}

---

Now produce the JSON due diligence report:"""


def analyse(
    company_text: str,
    signals_text: str,
    company_name: str = "Unknown",
) -> dict:
    """
    Run Gemini analysis on company context + signals.
    Returns parsed DD report dict.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Run: pip install google-generativeai")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = DD_PROMPT.format(
        company_text=company_text[:12000],
        signals_text=signals_text[:2000],
    )

    logger.info(f"Sending to Gemini: {len(prompt)} chars")

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Low temp = more consistent, factual
                max_output_tokens=8000,
            ),
        )

        raw = response.text.strip()

        # Strip markdown code blocks if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        report = json.loads(raw)
        logger.success(f"Gemini analysis complete: verdict={report.get('verdict')}")
        return {"success": True, "report": report, "raw": raw}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        logger.debug(f"Raw response: {raw[:500]}")
        return {"success": False, "error": f"JSON parse error: {e}", "raw": raw}

    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        return {"success": False, "error": str(e)}
