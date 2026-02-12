from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json

print("🔍 Debugging vector store search...")

# Load the recreated vector store
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./tally_chroma_db",
    embedding_function=embeddings
)

# Test different search queries
queries = [
    "security and user permissions",
    "Alt+K security",
    "TallyPrime security setup",
    "user creation and role assignment",
    "external applications integration",
    "API ODBC XML DLL"
]

for query in queries:
    print(f"\n🔎 Query: '{query}'")
    results = vectorstore.similarity_search(query, k=3)
    
    print(f"   Found {len(results)} results:")
    for i, doc in enumerate(results):
        title = doc.metadata.get("title", "Unknown")
        content_preview = doc.page_content[:100].replace('\n', ' ')
        print(f"   {i+1}. {title[:50]}...")
        print(f"      Preview: {content_preview}...")

# Also check total documents in vector store
print(f"\n📊 Total documents in vector store: {vectorstore._collection.count()}")

# Load original docs to compare
with open("tally_docs.json", "r", encoding="utf-8") as f:
    docs = json.load(f)

security_docs = [doc for doc in docs if 'security' in doc.get('title', '').lower()]
integration_docs = [doc for doc in docs if 'integration' in doc.get('title', '').lower() or 'api' in doc.get('title', '').lower()]

print(f"\n📒 Security docs in JSON: {len(security_docs)}")
print(f"🔗 Integration docs in JSON: {len(integration_docs)}")

for doc in security_docs[:2]:
    print(f"   - {doc['title']}")

for doc in integration_docs[:2]:
    print(f"   - {doc['title']}")
