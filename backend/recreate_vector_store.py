from qa_system import TallyQASystem
import json

print("🔄 Recreating vector store with new bank reconciliation content...")

try:
    # Initialize QA system
    qa_system = TallyQASystem()
    
    # Load documents (including new bank reconciliation content)
    documents = qa_system.load_documents()
    print(f"Loaded {len(documents)} documents total")
    
    # Create new vector store
    qa_system.create_vectorstore()
    print("✅ Vector store recreated successfully")
    
    # Test search for bank reconciliation
    results = qa_system.vectorstore.similarity_search("bank reconciliation procedures", k=3)
    print(f"\n🔍 Found {len(results)} relevant documents:")
    for i, doc in enumerate(results):
        title = doc.metadata.get("title", "Unknown")
        source = doc.metadata.get("source", "Unknown")
        print(f"{i+1}. {title}")
        print(f"   Source: {source}")
    
    print("\n✅ Vector store now includes bank reconciliation content!")
    print("🎯 Restart your backend server and try asking about bank reconciliation again.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
