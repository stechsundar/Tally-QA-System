"""
prime_scraper.py
Clean TallyPrime-only crawler for building tally_docs.json
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from datetime import datetime

BASE_URL = "https://help.tallysolutions.com"
START_URL = "https://help.tallysolutions.com/tally-prime/"

visited_urls = set()
valid_docs = []
MAX_PAGES = 800  # safety limit

if os.path.exists("tally_docs.json"):
    with open("tally_docs.json", "r", encoding="utf-8") as f:
        valid_docs.extend(json.load(f))
    visited_urls.update(doc["url"] for doc in valid_docs)
    print(f"🔄 Resuming from {len(valid_docs)} saved docs")


# =========================
# URL VALIDATION
# =========================
def is_valid_prime_url(url):
    url = url.lower()

    if not url.startswith(BASE_URL):
        return False

    # Reject unwanted sections
    blocked_keywords = [
        "tally.erp9",
        "shoper9",
        "developer-reference",
        "/faq",
        "?s=",
        "wp-content",
        ".jpg",
        ".png",
        ".gif",
        ".pdf",
        ".zip"
    ]

    for keyword in blocked_keywords:
        if keyword in url:
            return False

    # Reject homepage
    if url.rstrip("/") == BASE_URL:
        return False

    return True


# =========================
# CONTENT VALIDATION
# =========================
def is_valid_content(content, title):
    content_lower = content.lower()

    if len(content) < 800:
        return False

    if "you searched for" in title.lower():
        return False

    return True


# =========================
# SCRAPE ARTICLE
# =========================
def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove navigation and unwanted elements
        for tag in soup(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        content = soup.get_text(separator="\n", strip=True)

        if not is_valid_content(content, title):
            return None

        return {
            "url": url,
            "title": title,
            "content": content,
            "category": "TallyPrime",
            "scraped_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None

def extract_content(url, soup):
    try:
        for tag in soup(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        # ---- Better title extraction ----
        title = ""

        # Try common patterns
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

        if not title:
            title = "Untitled"

        content = soup.get_text(separator="\n", strip=True)

        print("Content length:", len(content))
        print("Title:", title)

        if not is_valid_content(content, title):
            print("❌ Rejected:", url)
            return None

        return {
            "url": url,
            "title": title,
            "content": content,
            "category": "TallyPrime",
            "scraped_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error extracting {url}: {e}")
        return None

# =========================
# CRAWLER
# =========================
def crawl(start_url):
    queue = [start_url]

    while queue and len(valid_docs) < MAX_PAGES:
        current_url = queue.pop(0)

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)

        if not is_valid_prime_url(current_url):
            continue

        print(f"🔍 Crawling: {current_url}")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(current_url, headers=headers, timeout=20)

            if response.status_code != 200:
                print(f"⚠️ Skipping {response.status_code}: {current_url}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # ---- Scrape content ----
            doc = extract_content(current_url, soup)

            if doc:
                print(f"✅ Saved: {doc['title']}")
                valid_docs.append(doc)
                with open("tally_docs.json", "w", encoding="utf-8") as f:
                    json.dump(valid_docs, f, indent=2, ensure_ascii=False)
                print("💾 Saved progress...")

            # ---- Discover links ----
            for a in soup.find_all("a", href=True):
                href = a["href"]
                new_url = urljoin(current_url, href)

                if new_url not in visited_urls and is_valid_prime_url(new_url):
                    queue.append(new_url)

        except Exception as e:
            print(f"❌ Error crawling {current_url}: {e}")

        time.sleep(0.3)


# =========================
# MAIN
# =========================
def main():
    print("🚀 Starting clean TallyPrime crawler...\n")

    crawl(START_URL)

    print("\n📊 Crawl complete")
    print(f"Total valid Prime articles collected: {len(valid_docs)}")

    with open("tally_docs.json", "w", encoding="utf-8") as f:
        json.dump(valid_docs, f, indent=2, ensure_ascii=False)

    print("✅ Clean tally_docs.json created successfully!")


if __name__ == "__main__":
    main()
