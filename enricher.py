"""
Veridian — Enricher
--------------------
Pulls free public signals to enrich the company profile:
  - HackerNews mentions
  - GitHub repos (if dev tool)
  - News mentions via HN Algolia
  - Similar company context

All free, no API keys needed.
"""

import requests
import time
from loguru import logger
from datetime import datetime, timedelta


def get_hn_mentions(company_name: str, domain: str = "") -> dict:
    """Search HackerNews for company mentions."""
    query = company_name
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": 5,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])

        mentions = []
        for h in hits:
            mentions.append({
                "title": h.get("title", ""),
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "date": h.get("created_at", ""),
            })

        total = data.get("nbHits", 0)
        logger.debug(f"HN: {total} mentions of '{company_name}'")
        return {"total": total, "top_posts": mentions}

    except Exception as e:
        logger.debug(f"HN lookup failed: {e}")
        return {"total": 0, "top_posts": []}


def get_github_signal(company_name: str, domain: str = "") -> dict:
    """Search GitHub for company repos."""
    try:
        # Search by org name
        org_name = domain.split(".")[0] if domain else company_name.lower().replace(" ", "")

        resp = requests.get(
            f"https://api.github.com/orgs/{org_name}/repos",
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "VeridianBot/1.0"},
            params={"sort": "stars", "per_page": 5},
            timeout=8,
        )

        if resp.status_code == 200:
            repos = resp.json()
            total_stars = sum(r.get("stargazers_count", 0) for r in repos)
            return {
                "found": True,
                "org": org_name,
                "public_repos": len(repos),
                "total_stars": total_stars,
                "top_repos": [
                    {"name": r["name"], "stars": r["stargazers_count"],
                     "description": r.get("description", "")}
                    for r in repos[:3]
                ],
            }

        # Fallback: search repos
        resp2 = requests.get(
            "https://api.github.com/search/repositories",
            headers={"Accept": "application/vnd.github.v3+json",
                     "User-Agent": "VeridianBot/1.0"},
            params={"q": f"org:{org_name}", "sort": "stars", "per_page": 3},
            timeout=8,
        )
        if resp2.status_code == 200:
            items = resp2.json().get("items", [])
            if items:
                return {
                    "found": True,
                    "org": org_name,
                    "total_stars": sum(i["stargazers_count"] for i in items),
                    "top_repos": [{"name": i["name"], "stars": i["stargazers_count"],
                                   "description": i.get("description", "")} for i in items],
                }

        return {"found": False}

    except Exception as e:
        logger.debug(f"GitHub lookup failed: {e}")
        return {"found": False}


def get_news_mentions(company_name: str) -> list:
    """Get recent news via HN Algolia (free)."""
    try:
        since = int((datetime.utcnow() - timedelta(days=90)).timestamp())
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": company_name,
                "numericFilters": f"created_at_i>{since}",
                "hitsPerPage": 3,
            },
            timeout=8,
        )
        hits = resp.json().get("hits", [])
        return [{"title": h.get("title", ""), "date": h.get("created_at", "")} for h in hits]
    except Exception:
        return []


def enrich(company_name: str, domain: str = "") -> dict:
    """
    Run all enrichment signals and return a combined profile.
    """
    logger.info(f"Enriching: {company_name}")

    hn = get_hn_mentions(company_name, domain)
    time.sleep(0.5)
    gh = get_github_signal(company_name, domain)
    time.sleep(6)  # GitHub rate limit
    news = get_news_mentions(company_name)

    signal_summary = f"""
PUBLIC SIGNAL ENRICHMENT FOR: {company_name}

HackerNews:
- Total mentions: {hn['total']}
- Top posts: {', '.join(p['title'] for p in hn['top_posts'][:3]) or 'None found'}

GitHub:
- Organisation found: {gh.get('found', False)}
- Total stars: {gh.get('total_stars', 'N/A')}
- Public repos: {gh.get('public_repos', 'N/A')}

Recent News (last 90 days):
{chr(10).join(f"- {n['title']}" for n in news) or '- No recent news found'}
"""

    return {
        "hn": hn,
        "github": gh,
        "news": news,
        "summary": signal_summary.strip(),
    }
