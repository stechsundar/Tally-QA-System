import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE_URL = "https://help.tallysolutions.com"
START_URL = "https://help.tallysolutions.com/tally-prime/"

visited = set()
valid_urls = set()

def is_valid_prime_url(url):
    url = url.lower()

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

    if not url.startswith(BASE_URL):
        return False

    for keyword in blocked_keywords:
        if keyword in url:
            return False

    return True


def discover_urls(start_url):
    queue = [start_url]

    while queue:
        current = queue.pop(0)

        if current in visited:
            continue

        visited.add(current)

        print("Checking:", current)

        try:
            response = requests.get(current, timeout=15)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for a in soup.find_all("a", href=True):
                new_url = urljoin(current, a["href"])

                if is_valid_prime_url(new_url):
                    if new_url not in visited:
                        queue.append(new_url)
                    valid_urls.add(new_url)

        except:
            continue

        time.sleep(0.3)

    print("\nTotal unique valid URLs found:", len(valid_urls))


if __name__ == "__main__":
    discover_urls(START_URL)
