"""
Veridian — Competitor Mapper
-----------------------------
After DD on a company, automatically finds and analyses
3 competitors using the same pipeline.

Returns a comparison table: scores, verdicts, differentiators.
"""

import os
import json
import re
import requests
from loguru import logger
from bs4 import BeautifulSoup


SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def find_competitors(company_name: str, description: str) -> list[str]:
    """
    Find competitor company names using DuckDuckGo instant answers
    and HN discussion mining. Returns list of company names.
    """
    competitors = []

    # Try DuckDuckGo search
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": f"{company_name} competitors alternatives",
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            headers=SEARCH_HEADERS,
            timeout=8,
        )
        data = resp.json()

        # Parse related topics
        for topic in data.get("RelatedTopics", [])[:10]:
            text = topic.get("Text", "")
            if text and len(text) > 10:
                # Extract company name from first word(s)
                name = text.split(" ")[0].strip(".,")
                if name and name.lower() != company_name.lower() and len(name) > 2:
                    competitors.append(name)
                    if len(competitors) >= 5:
                        break

    except Exception as e:
        logger.debug(f"DuckDuckGo search failed: {e}")

    # Fallback: search HN for competitor mentions
    if len(competitors) < 3:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": f"{company_name} vs alternative",
                    "tags": "story",
                    "hitsPerPage": 5,
                },
                timeout=8,
            )
            for hit in resp.json().get("hits", []):
                title = hit.get("title", "")
                # Extract "X vs Y" patterns
                vs_match = re.search(r"(\w+)\s+vs\.?\s+(\w+)", title, re.I)
                if vs_match:
                    for g in [vs_match.group(1), vs_match.group(2)]:
                        if g.lower() != company_name.lower() and g not in competitors:
                            competitors.append(g)
        except Exception:
            pass

    return competitors[:5]


def analyse_competitor(
    company_name: str,
    main_company: str,
    main_description: str,
) -> dict:
    """
    Run a lightweight analysis on a competitor.
    Uses Gemini with a shorter prompt focused on comparison.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "No API key"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are a VC analyst comparing competitors.

Main company being evaluated: {main_company}
Main company description: {main_description[:500]}

Competitor to analyse: {company_name}

Provide a brief competitive analysis in this JSON format only:
{{
  "name": "{company_name}",
  "one_liner": "what they do in one sentence",
  "stage": "early/growth/mature/public",
  "funding": "estimated funding stage or amount if known",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "vs_main": "how they compare to {main_company} — who has the edge and why",
  "threat_level": "LOW" | "MEDIUM" | "HIGH",
  "market_score": 1-10
}}

Be concise and honest. JSON only, no preamble."""

        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=800,
            ),
        )

        raw = resp.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except Exception as e:
        logger.warning(f"Competitor analysis failed for {company_name}: {e}")
        return {
            "name": company_name,
            "one_liner": "Analysis unavailable",
            "threat_level": "UNKNOWN",
            "market_score": 0,
            "error": str(e),
        }


def map_competitors(
    company_name: str,
    description: str,
    n: int = 3,
) -> list[dict]:
    """
    Find and analyse N competitors.
    Returns list of competitor analysis dicts.
    """
    logger.info(f"Mapping competitors for: {company_name}")

    names = find_competitors(company_name, description)
    logger.info(f"Found competitors: {names[:n]}")

    results = []
    for name in names[:n]:
        analysis = analyse_competitor(name, company_name, description)
        results.append(analysis)

    return results
