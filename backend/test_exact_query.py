from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing exact query: 'Integration with external systems'")

# Load the vector store
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./tally_chroma_db",
    embedding_function=embeddings
)

# Test the exact query
query = "Integration with external systems"
print(f"🔎 Query: '{query}'")
results = vectorstore.similarity_search(query, k=5)

print(f"   Found {len(results)} results:")
for i, doc in enumerate(results):
    title = doc.metadata.get("title", "Unknown")
    source = doc.metadata.get("source", "Unknown")
    content_preview = doc.page_content[:200].replace('\n', ' ')
    print(f"\n{i+1}. {title}")
    print(f"   Source: {source}")
    print(f"   Preview: {content_preview}...")

# Test with QA system
print(f"\n🤖 Testing QA system...")
try:
    from qa_system import TallyQASystem
    qa_system = TallyQASystem()
    qa_system.load_vectorstore()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        qa_system.create_qa_chain(api_key)
        result = qa_system.ask(query)
        print(f"Answer: {result['short_answer']}")
        
        # Check if answer mentions APIs, ODBC, etc.
        answer_lower = result['short_answer'].lower()
        if any(term in answer_lower for term in ['api', 'odbc', 'xml', 'dll', 'integration']):
            print("✅ Answer contains integration terms")
        else:
            print("❌ Answer missing integration terms")
    else:
        print("❌ No API key - cannot test QA")
        
except Exception as e:
    print(f"❌ QA test error: {e}")
