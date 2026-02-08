import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque
import json

class TallyDocScraper:
    def __init__(self, base_url="https://help.tallysolutions.com/"):
        self.base_url = base_url
        self.visited_urls = set()
        self.to_visit = deque([base_url])
        self.scraped_data = []
        
    def is_valid_url(self, url):
        """Check if URL belongs to Tally help domain"""
        parsed = urlparse(url)
        return parsed.netloc == "help.tallysolutions.com"
    
    def scrape_page(self, url):
        """Scrape content from a single page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else ""
            
            # Get main content area - adjust selectors based on actual site
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_='content') or
                soup.find('div', id='content')
            )
            
            if not main_content:
                main_content = soup.body
            
            # Remove unwanted elements
            for element in main_content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Extract text
            text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up extra whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                if self.is_valid_url(absolute_url) and '#' not in absolute_url:
                    links.append(absolute_url)
            
            # Extract breadcrumb or category if available
            breadcrumb = soup.find('nav', class_='breadcrumb') or soup.find('ol', class_='breadcrumb')
            category = ""
            if breadcrumb:
                category = breadcrumb.get_text(separator=' > ', strip=True)
            
            return {
                'url': url,
                'title': title_text,
                'content': text,
                'category': category,
                'links': list(set(links))  # Remove duplicates
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def crawl(self, max_pages=500):
        """Crawl the documentation site"""
        page_count = 0
        
        while self.to_visit and page_count < max_pages:
            url = self.to_visit.popleft()
            
            if url in self.visited_urls:
                continue
            
            print(f"Scraping ({page_count + 1}/{max_pages}): {url}")
            self.visited_urls.add(url)
            
            page_data = self.scrape_page(url)
            
            if page_data and len(page_data['content']) > 100:  # Skip empty pages
                self.scraped_data.append(page_data)
                
                # Add new links to queue
                for link in page_data['links']:
                    if link not in self.visited_urls:
                        self.to_visit.append(link)
                
                page_count += 1
                time.sleep(1)  # Be respectful to the server
        
        return self.scraped_data
    
    def save_to_file(self, filename='tally_docs.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.scraped_data)} documents to {filename}")

# Run the scraper
scraper = TallyDocScraper()
docs = scraper.crawl(max_pages=500)
scraper.save_to_file('tally_docs.json')