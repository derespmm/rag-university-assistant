# Scrapes the Miami University Policy Library and saves each policy page as a
# PDF in data/policies/. Run this once to populate the policy corpus, and
# re-run whenever policies are updated.
#
# Usage:
#   python scripts/scrape_policies.py
#
# Requirements:
#   uv pip install playwright beautifulsoup4 requests
#   playwright install chromium

import asyncio
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright
from tqdm import tqdm

BASE_URL = "https://miamioh.edu/policy-library/"
OUTPUT_DIR = Path("data/policies")


def collect_policy_urls() -> list[tuple[str, str]]:
    """
    Fetch the policy library index (static HTML) and return all policy URLs.

    Returns a list of (url, filename) tuples where filename is a sanitized
    version of the relative path used as the output PDF name.
    """
    print("Fetching policy index...")
    response = requests.get(BASE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # all policy links are relative hrefs inside the main content container
    container = soup.select_one("div.sidebar-layout__components-inner")
    if not container:
        raise RuntimeError("Could not find policy container — page structure may have changed.")

    urls = []
    for a in container.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = str(a.get("href", "")).strip()
        # skip anchor-only links (section jumps) and external links
        if not href or href.startswith("#") or href.startswith("http"):
            continue

        full_url = BASE_URL + href

        # turn "academics/curriculum/changes-to-academic-curriculum.html"
        # into "academics__curriculum__changes-to-academic-curriculum.pdf"
        filename = re.sub(r"[/\\]", "__", href)
        filename = re.sub(r"\.html?$", ".pdf", filename)
        filename = re.sub(r"[^\w\-.]", "_", filename)

        urls.append((full_url, filename))

    print(f"Found {len(urls)} policy pages.")
    return urls


async def save_as_pdf(page, url: str, output_path: Path) -> None:
    """
    Load a policy page in a headless browser and save it as a PDF.
    Skips the page if the PDF already exists.
    """
    if output_path.exists():
        return

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=False,
        )
    except Exception as e:
        print(f"\n  [warning] failed to save {url}: {e}")


async def scrape_all(urls: list[tuple[str, str]]) -> None:
    """
    Launch a single headless browser and render all policy pages to PDF.
    Reuses one browser context for efficiency.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for url, filename in tqdm(urls, desc="Saving PDFs"):
            output_path = OUTPUT_DIR / filename
            await save_as_pdf(page, url, output_path)

        await browser.close()

    saved = len(list(OUTPUT_DIR.glob("*.pdf")))
    print(f"\nDone. {saved} PDFs saved to {OUTPUT_DIR}/")


def main():
    urls = collect_policy_urls()
    asyncio.run(scrape_all(urls))


if __name__ == "__main__":
    main()
