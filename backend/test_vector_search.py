from qa_system import TallyQASystem
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing vector store search for security content...")

try:
    qa_system = TallyQASystem()
    qa_system.load_vectorstore()
    
    # Test search for security
    print("\n🔎 Searching for 'security and user permissions':")
    results = qa_system.vectorstore.similarity_search("security and user permissions", k=3)
    
    print(f"Found {len(results)} documents:")
    for i, doc in enumerate(results):
        title = doc.metadata.get("title", "Unknown")
        source = doc.metadata.get("source", "Unknown")
        content_preview = doc.page_content[:200].replace('\n', ' ')
        
        print(f"\n{i+1}. {title}")
        print(f"   Source: {source}")
        print(f"   Preview: {content_preview}...")
        
        if 'Alt+K' in doc.page_content:
            print("   ✅ Contains Alt+K")
        else:
            print("   ❌ No Alt+K found")
    
    # Test with API key if available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"\n🤖 Testing QA with security question:")
        qa_system.create_qa_chain(api_key)
        result = qa_system.ask("How do I set up security and user permissions in TallyPrime?")
        print(f"Answer: {result['short_answer']}")
        
        if 'Alt+K' in result['short_answer'] or 'Alt+K' in result['long_answer']:
            print("✅ AI response includes Alt+K")
        else:
            print("❌ AI response does not include Alt+K")
    else:
        print("\n⚠️ No ANTHROPIC_API_KEY found - cannot test QA")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
