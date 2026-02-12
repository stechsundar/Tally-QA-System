import json
import os

# Check if bank reconciliation content was added
with open('tally_docs.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

bank_docs = [doc for doc in docs if 'bank' in doc.get('title', '').lower() or 'reconciliation' in doc.get('title', '').lower()]

print(f'Found {len(bank_docs)} bank reconciliation documents:')
for doc in bank_docs:
    print(f'- {doc["title"]}')
    print(f'  URL: {doc["url"]}')
    print()

# Test vector store loading
try:
    from qa_system import TallyQASystem
    qa_system = TallyQASystem()
    qa_system.load_vectorstore()
    
    # Test search
    results = qa_system.vectorstore.similarity_search("bank reconciliation", k=3)
    print(f'Found {len(results)} relevant documents in vector store:')
    for i, doc in enumerate(results):
        print(f'{i+1}. {doc.metadata.get("title", "Unknown")}')
        print(f'   Source: {doc.metadata.get("source", "Unknown")}')
        print()
        
except Exception as e:
    print(f'Error loading vector store: {e}')
