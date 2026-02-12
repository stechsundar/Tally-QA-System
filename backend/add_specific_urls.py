import json
import requests
from bs4 import BeautifulSoup
import html2text
import os
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

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
            title = "Unknown Title"
            
        return {
            'title': title,
            'content': content,
            'url': url,
            'category': 'Additional',
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_specific_urls():
    """Add specific URLs to existing knowledge base"""
    
    # URLs you want to add
    urls_to_add = [
        "https://help.tallysolutions.com/?geot_debug=IN&cat_id=23&s=Security+and+user+permissions+setup",
        "https://help.tallysolutions.com/?geot_debug=IN&cat_id=23&s=Bank+reconciliation+procedures",
        # Add more URLs here as needed
    ]
    
    print("🔍 Adding specific URLs to knowledge base...")
    
    # Load existing documents
    with open("tally_docs.json", "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    print(f"📚 Current documents: {len(docs)}")
    
    # Add new URLs
    added_count = 0
    for url in urls_to_add:
        # Check if URL already exists
        existing_urls = {doc.get('url') for doc in docs}
        if url in existing_urls:
            print(f"⚠️  URL already exists: {url}")
            continue
        
        # Scrape new content
        print(f"🔍 Scraping: {url}")
        new_doc = scrape_tally_url(url)
        
        if new_doc:
            docs.append(new_doc)
            added_count += 1
            print(f"✅ Added: {new_doc['title']}")
        else:
            print(f"❌ Failed to scrape: {url}")
    
    # Save updated knowledge base
    with open("tally_docs.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Added {added_count} new documents")
    print(f"📚 Total documents: {len(docs)}")
    
    return docs

def update_vector_store(docs):
    """Update vector store with all documents"""
    print("\n🔄 Updating vector store...")
    
    # Convert to LangChain documents
    documents = [
        Document(
            page_content=item["content"],
            metadata={
                "source": item["url"],
                "title": item["title"],
                "category": item.get("category", "")
            },
        )
        for item in docs
    ]
    
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)
    print(f"📄 Split into {len(splits)} chunks")
    
    # Create new vector store
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./tally_chroma_db"
    )
    
    print("✅ Vector store updated successfully")
    return vectorstore

def main():
    print("🎯 Adding specific URLs without losing existing content\n")
    
    # Add specific URLs
    docs = add_specific_urls()
    
    # Update vector store
    update_vector_store(docs)
    
    print("\n🚀 Done! Restart backend server to use updated content")

if __name__ == "__main__":
    main()
