"""
add_bank_reconciliation.py - Add bank reconciliation content to Tally AI knowledge base
"""

import json
import requests
from bs4 import BeautifulSoup
import html2text
import os
from datetime import datetime

def scrape_tally_url(url):
    """Scrape content from Tally help URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove navigation, header, footer elements
        for element in soup(['nav', 'header', 'footer', 'script', 'style']):
            element.decompose()
        
        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0
        
        content = h.handle(str(soup))
        
        # Get title
        title = soup.find('title')
        if title:
            title = title.get_text().strip()
        else:
            title = "Bank Reconciliation Procedures"
            
        return {
            'title': title,
            'content': content,
            'url': url,
            'category': 'Banking',
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_to_knowledge_base(new_doc):
    """Add new document to existing knowledge base"""
    docs_file = "tally_docs.json"
    
    # Load existing documents
    existing_docs = []
    if os.path.exists(docs_file):
        with open(docs_file, 'r', encoding='utf-8') as f:
            existing_docs = json.load(f)
    
    # Check if URL already exists
    existing_urls = {doc.get('url') for doc in existing_docs}
    if new_doc['url'] in existing_urls:
        print(f"URL {new_doc['url']} already exists in knowledge base")
        return False
    
    # Add new document
    existing_docs.append(new_doc)
    
    # Save updated knowledge base
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(existing_docs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Added '{new_doc['title']}' to knowledge base")
    return True

def update_vector_store():
    """Update the vector store with new content"""
    try:
        from qa_system import TallyQASystem
        
        qa_system = TallyQASystem()
        qa_system.load_documents()
        qa_system.create_vector_store()
        
        print("✅ Vector store updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating vector store: {e}")
        return False

def main():
    # Bank reconciliation URL
    bank_reconciliation_url = "https://help.tallysolutions.com/?geot_debug=IN&cat_id=23&s=Bank+reconciliation+procedures"
    
    print("🔍 Scraping bank reconciliation content...")
    
    # Scrape the content
    new_doc = scrape_tally_url(bank_reconciliation_url)
    
    if not new_doc:
        print("❌ Failed to scrape content")
        return
    
    # Add to knowledge base
    if add_to_knowledge_base(new_doc):
        print(f"\n📄 Content preview:")
        print(f"Title: {new_doc['title']}")
        print(f"URL: {new_doc['url']}")
        print(f"Content length: {len(new_doc['content'])} characters")
        print(f"First 200 chars: {new_doc['content'][:200]}...")
        
        # Update vector store
        print("\n🔄 Updating vector store...")
        update_vector_store()
        
        print("\n✅ Bank reconciliation content added successfully!")
        print("🎯 You can now ask questions about bank reconciliation")
    else:
        print("❌ Failed to add content to knowledge base")

if __name__ == "__main__":
    main()
