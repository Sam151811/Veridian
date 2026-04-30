"""
Veridian — LinkedIn Enrichment
--------------------------------
Enriches founder analysis using public LinkedIn data.
Uses scraping since LinkedIn has no free API.

Falls back gracefully if LinkedIn blocks the request.
"""

import re
import requests
import time
from loguru import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}


def extract_linkedin_profile(url: str) -> dict:
    """
    Extract public profile data from a LinkedIn URL.
    LinkedIn is aggressive — this uses Playwright for best results.
    Falls back to basic request if Playwright unavailable.
    """
    if not url:
        return {"success": False, "error": "No URL provided"}

    # Try Playwright first
    try:
        return _scrape_with_playwright(url)
    except Exception as e:
        logger.debug(f"Playwright LinkedIn failed: {e}")

    # Fallback: basic request (often blocked but worth trying)
    try:
        return _scrape_basic(url)
    except Exception as e:
        logger.debug(f"Basic LinkedIn scrape failed: {e}")

    return {
        "success": False,
        "error": "LinkedIn blocked automated access. Paste founder bio manually.",
    }


def _scrape_with_playwright(url: str) -> dict:
    from playwright.sync_api import sync_playwright
    import time

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
            time.sleep(3)

            # Check if we hit a login wall
            content = page.content()
            if "authwall" in page.url or "login" in page.url:
                browser.close()
                return {"success": False, "error": "LinkedIn requires login to view profiles"}

            text = page.inner_text("body")
            text = re.sub(r"\s+", " ", text).strip()
            browser.close()

            if len(text) < 200:
                return {"success": False, "error": "Profile content too short — likely blocked"}

            return {
                "success": True,
                "text": text[:3000],
                "url": url,
            }

        except Exception as e:
            browser.close()
            raise e


def _scrape_basic(url: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return {"success": False, "error": f"HTTP {resp.status_code}"}

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 200:
        return {"success": False, "error": "No profile content extracted"}

    return {"success": True, "text": text[:3000], "url": url}


def analyse_founder(
    linkedin_text: str,
    company_name: str,
    company_description: str,
) -> dict:
    """
    Use Gemini to analyse founder background against the company's problem.
    Returns structured founder-market fit assessment.
    """
    import os, json
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "No API key"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are a VC analyst assessing founder-market fit.

Company: {company_name}
Company description: {company_description[:400]}

Founder LinkedIn profile text:
{linkedin_text[:2000]}

Analyse the founder's background and assess their fit for this problem.
Return JSON only:
{{
  "name": "founder name if found",
  "background_summary": "2-3 sentence summary of their background",
  "relevant_experience": ["experience 1", "experience 2"],
  "domain_expertise": "HIGH" | "MEDIUM" | "LOW",
  "prior_founder_experience": true | false,
  "top_school_or_company": true | false,
  "founder_market_fit_score": 1-10,
  "founder_market_fit_reasoning": "why they are or aren't the right person for this",
  "red_flags": ["flag 1"],
  "green_flags": ["flag 1"]
}}"""

        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2, max_output_tokens=600
            ),
        )

        raw = resp.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except Exception as e:
        logger.warning(f"Founder analysis failed: {e}")
        return {"error": str(e)}


def enrich_founder(
    linkedin_url: str,
    company_name: str,
    company_description: str,
) -> dict:
    """Main entry point — scrape LinkedIn and analyse founder."""
    logger.info(f"Enriching founder: {linkedin_url}")

    profile = extract_linkedin_profile(linkedin_url)

    if not profile.get("success"):
        return {
            "success": False,
            "error": profile.get("error", "Failed to fetch LinkedIn profile"),
        }

    analysis = analyse_founder(
        profile["text"],
        company_name,
        company_description,
    )

    return {
        "success": True,
        "analysis": analysis,
        "profile_url": linkedin_url,
    }
