"""
Veridian — Ingest
-----------------
Uses Playwright headless browser to scrape JavaScript-rendered sites.
Works on virtually any modern website.
"""

import re
import time
from loguru import logger


MAX_CHARS = 15000


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def scrape_url(url: str) -> dict:
    """Scrape using Playwright — handles JS-rendered sites."""
    if not url.startswith("http"):
        url = "https://" + url

    domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError("Run: pip install playwright && python -m playwright install chromium")

    pages_text = []
    urls_to_try = [url, f"https://{domain}/about", f"https://{domain}/team"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()

            for page_url in urls_to_try[:2]:
                try:
                    page.goto(page_url, wait_until="networkidle", timeout=15000)
                    time.sleep(2)  # Let JS render

                    # Remove noise elements
                    page.evaluate("""
                        ['nav','footer','header','script','style','iframe'].forEach(tag => {
                            document.querySelectorAll(tag).forEach(el => el.remove())
                        })
                    """)

                    text = page.inner_text("body")
                    text = clean_text(text)

                    if len(text) > 200:
                        pages_text.append(text[:5000])
                        logger.debug(f"Got {len(text)} chars from {page_url}")

                except Exception as e:
                    logger.debug(f"Page {page_url} failed: {e}")
                    continue

            browser.close()

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "source": url,
            "type": "url",
            "error": str(e),
        }

    if not pages_text:
        return {
            "success": False,
            "text": "",
            "source": url,
            "type": "url",
            "error": "No content extracted. Try uploading a PDF instead.",
        }

    combined = "\n\n---\n\n".join(pages_text)[:MAX_CHARS]
    logger.success(f"Scraped {url}: {len(combined)} chars")

    return {
        "success": True,
        "text": combined,
        "source": url,
        "type": "url",
        "domain": domain,
    }


def read_pdf(file) -> dict:
    """Extract text from an uploaded PDF pitch deck."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("Run: pip install pypdf")

    try:
        reader = PdfReader(file)
        pages_text = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                pages_text.append(f"[Slide {i+1}] {text}")

        if not pages_text:
            return {
                "success": False,
                "text": "",
                "source": "pdf",
                "type": "pdf",
                "error": "No text extracted. PDF may be image-based.",
            }

        combined = "\n\n".join(pages_text)[:MAX_CHARS]
        logger.success(f"PDF: {len(reader.pages)} pages, {len(combined)} chars")

        return {
            "success": True,
            "text": combined,
            "source": "pdf",
            "type": "pdf",
            "n_pages": len(reader.pages),
        }

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "source": "pdf",
            "type": "pdf",
            "error": str(e),
        }


def extract_company_name(text: str, url: str = "") -> str:
    if url:
        domain = url.replace("https://", "").replace("http://", "").replace("www.", "")
        name = domain.split(".")[0].replace("-", " ").title()
        if len(name) > 2:
            return name
    first_line = text.split("\n")[0][:60].strip()
    return first_line if first_line else "Unknown Company"
