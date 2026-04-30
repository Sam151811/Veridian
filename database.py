"""
Veridian — Database
--------------------
Supabase integration for saving and retrieving DD reports.
All reports saved with company name, verdict, scores, full JSON.

Tables:
  reports — full DD reports
  batch_runs — batch analysis sessions
"""

import os
import json
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
load_dotenv()


SCHEMA_SQL = """
-- Reports table
create table if not exists reports (
    id            bigserial primary key,
    company_name  text not null,
    verdict       text,
    confidence    text,
    overall_score float,
    market_score  float,
    team_score    float,
    product_score float,
    traction_score float,
    one_liner     text,
    tldr          text,
    recommendation text,
    full_report   jsonb,
    source_url    text,
    source_type   text,
    created_at    timestamptz default now()
);

-- Batch runs table
create table if not exists batch_runs (
    id            bigserial primary key,
    run_name      text,
    companies     jsonb,
    results       jsonb,
    created_at    timestamptz default now()
);

-- Enable full text search on reports
create index if not exists reports_company_name_idx on reports(company_name);
create index if not exists reports_verdict_idx on reports(verdict);
create index if not exists reports_created_at_idx on reports(created_at desc);
"""


def get_client():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key or "your-project" in url:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning(f"Supabase connection failed: {e}")
        return None


def print_schema():
    print("=" * 60)
    print("Run this SQL in Supabase → SQL Editor:")
    print("=" * 60)
    print(SCHEMA_SQL)
    print("=" * 60)


def save_report(report: dict, source_url: str = "", source_type: str = "url") -> bool:
    """Save a DD report to Supabase."""
    client = get_client()
    if not client:
        logger.debug("Supabase not configured — report not saved")
        return False

    sections = report.get("sections", {})
    try:
        client.table("reports").insert({
            "company_name":   report.get("company_name", "Unknown"),
            "verdict":        report.get("verdict", ""),
            "confidence":     report.get("confidence", ""),
            "overall_score":  float(report.get("overall_score", 0)),
            "market_score":   float(sections.get("market", {}).get("score", 0)),
            "team_score":     float(sections.get("team", {}).get("score", 0)),
            "product_score":  float(sections.get("product", {}).get("score", 0)),
            "traction_score": float(sections.get("traction", {}).get("score", 0)),
            "one_liner":      report.get("one_line_verdict", ""),
            "tldr":           report.get("tldr", ""),
            "recommendation": report.get("recommendation", ""),
            "full_report":    json.dumps(report),
            "source_url":     source_url,
            "source_type":    source_type,
        }).execute()
        logger.success(f"Report saved: {report.get('company_name')}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return False


def fetch_reports(limit: int = 50) -> list[dict]:
    """Fetch recent reports from Supabase."""
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("reports").select(
            "id, company_name, verdict, overall_score, market_score, "
            "team_score, product_score, traction_score, one_liner, "
            "tldr, recommendation, source_url, created_at"
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        return []


def fetch_report_by_id(report_id: int) -> dict | None:
    """Fetch a full report by ID."""
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("reports").select("*").eq("id", report_id).single().execute()
        if result.data and result.data.get("full_report"):
            return json.loads(result.data["full_report"])
        return None
    except Exception as e:
        logger.error(f"Failed to fetch report {report_id}: {e}")
        return None


def save_batch(run_name: str, companies: list, results: list) -> bool:
    """Save a batch run to Supabase."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("batch_runs").insert({
            "run_name":  run_name,
            "companies": json.dumps(companies),
            "results":   json.dumps(results),
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save batch: {e}")
        return False


def fetch_batches(limit: int = 10) -> list[dict]:
    """Fetch recent batch runs."""
    client = get_client()
    if not client:
        return []
    try:
        result = client.table("batch_runs").select(
            "id, run_name, created_at"
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception as e:
        return []
