from qa_system import TallyQASystem
import shutil
import os

print("🗑️  Deleting old vector store...")

# Delete old vector store
if os.path.exists("./tally_chroma_db"):
    shutil.rmtree("./tally_chroma_db")
    print("✅ Old vector store deleted")
else:
    print("⚠️  No existing vector store found")

print("\n🔄 Creating new vector store with bank reconciliation content...")

try:
    # Initialize QA system
    qa_system = TallyQASystem()
    
    # Load documents (including new bank reconciliation content)
    documents = qa_system.load_documents()
    print(f"📚 Loaded {len(documents)} documents total")
    
    # Create fresh vector store
    qa_system.create_vectorstore()
    print("✅ New vector store created successfully")
    
    # Test search for bank reconciliation
    results = qa_system.vectorstore.similarity_search("bank reconciliation procedures", k=3)
    print(f"\n🔍 Found {len(results)} relevant documents:")
    for i, doc in enumerate(results):
        title = doc.metadata.get("title", "Unknown")
        source = doc.metadata.get("source", "Unknown")
        print(f"{i+1}. {title}")
        print(f"   Source: {source}")
    
    print("\n🎯 Vector store now includes bank reconciliation content!")
    print("🔄 Restart your backend server to use the new vector store.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
