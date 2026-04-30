"""
Veridian — Batch Analyser
--------------------------
Analyse multiple companies at once.
Returns a ranked comparison table.

Input: list of URLs or company descriptions
Output: ranked DataFrame with scores + verdicts
"""

import time
import pandas as pd
from loguru import logger
from datetime import datetime


def run_batch(
    companies: list[dict],
    enrich: bool = False,
    delay: float = 2.0,
) -> list[dict]:
    """
    Analyse multiple companies.

    companies = [
        {"name": "Stripe", "url": "https://stripe.com"},
        {"name": "Airbnb", "url": "https://airbnb.com"},
        ...
    ]

    Returns list of result dicts with report + metadata.
    """
    from src.ingest import scrape_url, extract_company_name
    from src.enricher import enrich as enrich_signals
    from src.analyst import analyse

    results = []

    for i, company in enumerate(companies):
        url = company.get("url", "")
        name = company.get("name", "")

        logger.info(f"Batch [{i+1}/{len(companies)}]: {name or url}")

        try:
            # Ingest
            if url:
                ingested = scrape_url(url)
                if not ingested["success"]:
                    results.append({
                        "name": name or url,
                        "url": url,
                        "success": False,
                        "error": ingested.get("error", "Ingest failed"),
                    })
                    continue
                company_name = name or extract_company_name(ingested["text"], url)
            else:
                # Use provided description directly
                ingested = {
                    "success": True,
                    "text": company.get("description", ""),
                    "type": "manual",
                }
                company_name = name

            # Signals
            signals_text = ""
            if enrich and url:
                domain = url.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
                signals = enrich_signals(company_name, domain)
                signals_text = signals.get("summary", "")
                time.sleep(1)

            # Analyse
            result = analyse(ingested["text"], signals_text, company_name)

            if result["success"]:
                report = result["report"]
                sections = report.get("sections", {})
                results.append({
                    "name": report.get("company_name", company_name),
                    "url": url,
                    "success": True,
                    "verdict": report.get("verdict", "—"),
                    "confidence": report.get("confidence", "—"),
                    "overall_score": report.get("overall_score", 0),
                    "market_score": sections.get("market", {}).get("score", 0),
                    "team_score": sections.get("team", {}).get("score", 0),
                    "product_score": sections.get("product", {}).get("score", 0),
                    "traction_score": sections.get("traction", {}).get("score", 0),
                    "one_liner": report.get("one_line_verdict", ""),
                    "recommendation": report.get("recommendation", ""),
                    "report": report,
                })
            else:
                results.append({
                    "name": company_name,
                    "url": url,
                    "success": False,
                    "error": result.get("error", "Analysis failed"),
                })

        except Exception as e:
            logger.error(f"Batch item failed: {e}")
            results.append({
                "name": name or url,
                "url": url,
                "success": False,
                "error": str(e),
            })

        # Polite delay between requests
        if i < len(companies) - 1:
            time.sleep(delay)

    logger.success(f"Batch complete: {sum(1 for r in results if r.get('success'))} / {len(results)} succeeded")
    return results


def to_dataframe(results: list[dict]) -> pd.DataFrame:
    """Convert batch results to a ranked comparison DataFrame."""
    rows = []
    for r in results:
        if r.get("success"):
            verdict_order = {"INVEST": 0, "WATCH": 1, "PASS": 2}.get(r.get("verdict", ""), 3)
            rows.append({
                "Company": r.get("name", ""),
                "Verdict": r.get("verdict", "—"),
                "Overall": r.get("overall_score", 0),
                "Market": r.get("market_score", 0),
                "Team": r.get("team_score", 0),
                "Product": r.get("product_score", 0),
                "Traction": r.get("traction_score", 0),
                "One-liner": r.get("one_liner", ""),
                "_verdict_order": verdict_order,
                "_url": r.get("url", ""),
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(["_verdict_order", "Overall"], ascending=[True, False])
    df = df.drop(columns=["_verdict_order"])
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    return df
