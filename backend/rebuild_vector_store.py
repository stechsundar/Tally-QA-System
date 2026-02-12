import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

print("📚 Loading updated documents...")

# Load documents from JSON
with open("tally_docs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

documents = [
    Document(
        page_content=item["content"],
        metadata={
            "source": item["url"],
            "title": item["title"],
            "category": item.get("category", "")
        },
    )
    for item in data
]

print(f"✅ Loaded {len(documents)} documents")

# Check security content
security_docs = [doc for doc in documents if 'security' in doc.metadata.get('title', '').lower()]
print(f"🔒 Found {len(security_docs)} security documents:")
for doc in security_docs:
    print(f"   - {doc.metadata['title']}")
    if 'Alt+K' in doc.page_content:
        print("     ✅ Contains Alt+K")

print("\n🔄 Creating new vector store...")

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

# Create vector store
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./tally_chroma_db"
)

print("✅ Vector store created successfully")

# Test search
print("\n🔍 Testing search for 'security and user permissions':")
results = vectorstore.similarity_search("security and user permissions", k=3)
print(f"Found {len(results)} results:")
for i, doc in enumerate(results):
    title = doc.metadata.get("title", "Unknown")
    print(f"{i+1}. {title}")
    if 'Alt+K' in doc.page_content:
        print("   ✅ Contains Alt+K")

print("\n🎯 Vector store is now updated with new content!")
print("🚀 Start the backend server to use the updated vector store")
