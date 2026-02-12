from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import json

print("🔍 Comparing old and new vector stores...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load old vector store
old_vectorstore = Chroma(
    persist_directory="./tally_chroma_db",
    embedding_function=embeddings
)

# Load new vector store  
new_vectorstore = Chroma(
    persist_directory="./tally_chroma_db_new",
    embedding_function=embeddings
)

old_count = old_vectorstore._collection.count()
new_count = new_vectorstore._collection.count()

print(f"📊 Old vector store: {old_count} documents")
print(f"📊 New vector store: {new_count} documents")
print(f"📉 Difference: {old_count - new_count} documents lost")

# Get sample documents from both stores
print(f"\n🔍 Sampling documents from old store...")
old_results = old_vectorstore.similarity_search("Tally", k=10)
print(f"Old store sample:")
for i, doc in enumerate(old_results[:5]):
    title = doc.metadata.get("title", "Unknown")
    source = doc.metadata.get("source", "Unknown")
    print(f"{i+1}. {title[:60]}...")
    print(f"   Source: {source[:80]}...")

print(f"\n🔍 Sampling documents from new store...")
new_results = new_vectorstore.similarity_search("Tally", k=10)
print(f"New store sample:")
for i, doc in enumerate(new_results[:5]):
    title = doc.metadata.get("title", "Unknown")
    source = doc.metadata.get("source", "Unknown")
    print(f"{i+1}. {title[:60]}...")
    print(f"   Source: {source[:80]}...")

# Check what URLs are in each
print(f"\n🔗 Analyzing sources...")

# Get all sources from old store
old_all = old_vectorstore.similarity_search("", k=old_count)
old_sources = set(doc.metadata.get("source", "") for doc in old_all)

# Get all sources from new store
new_all = new_vectorstore.similarity_search("", k=new_count)
new_sources = set(doc.metadata.get("source", "") for doc in new_all)

# Find lost sources
lost_sources = old_sources - new_sources
print(f"\n❌ Lost sources ({len(lost_sources)}):")
for source in sorted(list(lost_sources))[:10]:
    print(f"   - {source}")

# Find new sources
gained_sources = new_sources - old_sources
print(f"\n✅ New sources ({len(gained_sources)}):")
for source in sorted(list(gained_sources)):
    print(f"   - {source}")

print(f"\n💡 Recommendation: Keep old store and add only specific new URLs")
