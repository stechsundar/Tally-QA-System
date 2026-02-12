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
            title = "Security and User Permissions Setup"
            
        return {
            'title': title,
            'content': content,
            'url': url,
            'category': 'Security',
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def update_security_content():
    """Replace old security content with new TallyPrime content"""
    docs_file = "tally_docs.json"
    
    # Load existing documents
    with open(docs_file, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    
    # Find old security-related documents
    old_security_docs = []
    for i, doc in enumerate(docs):
        title = doc.get('title', '').lower()
        content = doc.get('content', '').lower()
        if ('security' in title or 'user' in title and 'permission' in title or 
            'tally.erp9' in doc.get('url', '').lower()):
            old_security_docs.append((i, doc))
            print(f"Found old security doc: {doc['title']}")
            print(f"  URL: {doc['url']}")
    
    # Remove old security documents
    docs = [doc for i, doc in enumerate(docs) if not any(i == old_idx for old_idx, _ in old_security_docs)]
    print(f"\n🗑️  Removed {len(old_security_docs)} old security documents")
    
    # Add new security content
    new_security_url = "https://help.tallysolutions.com/?geot_debug=IN&cat_id=23&s=Security+and+user+permissions+setup"
    
    print(f"\n🔍 Scraping new security content...")
    new_doc = scrape_tally_url(new_security_url)
    
    if new_doc:
        docs.append(new_doc)
        print(f"✅ Added new security document: {new_doc['title']}")
        print(f"  URL: {new_doc['url']}")
        print(f"  Content length: {len(new_doc['content'])} characters")
    
    # Save updated knowledge base
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated knowledge base with {len(docs)} total documents")
    return True

def main():
    print("🔄 Updating Security and User Permissions content...")
    print("Replacing old Tally.ERP9 content with new TallyPrime content\n")
    
    if update_security_content():
        print("\n✅ Security content updated successfully!")
        print("🎯 Next steps:")
        print("1. Stop the backend server (Ctrl+C)")
        print("2. Delete the vector store: Remove-Item -Recurse -Force tally_chroma_db")
        print("3. Restart the backend server")
        print("4. Test with questions about security and user permissions")
    else:
        print("❌ Failed to update security content")

if __name__ == "__main__":
    main()
