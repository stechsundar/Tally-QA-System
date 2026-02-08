"""
main.py - Interactive Tally Q&A System
Run this THIRD to ask questions about Tally
"""

import os
from dotenv import load_dotenv
from qa_system import TallyQASystem

def main():
    print("\n" + "="*80)
    print("Tally Q&A System - Interactive Mode")
    print("="*80)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_api_key:
        print("\n❌ Error: ANTHROPIC_API_KEY not found!")
        print("\nPlease create a .env file with:")
        print("ANTHROPIC_API_KEY=your-api-key-here")
        return
    
    # Initialize system
    print("\nInitializing Tally Q&A System...")
    qa_system = TallyQASystem()
    
    try:
        # Load vector store
        qa_system.load_vectorstore()
        
        # Create QA chain
        qa_system.create_qa_chain(anthropic_api_key)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease complete these steps first:")
        print("1. Run 'python scraper.py' to scrape Tally documentation")
        print("2. Run 'python qa_system.py' to create vector store")
        return
    
    print("\n" + "="*80)
    print("✓ System Ready! Ask questions about Tally.")
    print("="*80)
    print("\nTips:")
    print("- Ask questions in natural language")
    print("- The system remembers conversation context")
    print("- Type 'quit' or 'exit' to stop")
    print("\nExample questions:")
    print("- How do I create a sales invoice in Tally?")
    print("- What is GST in Tally?")
    print("- How to generate balance sheet?")
    print("="*80 + "\n")
    
    # Interactive loop
    while True:
        question = input("\n💬 Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q', 'bye']:
            print("\n👋 Goodbye!")
            break
        
        if not question:
            continue
        
        try:
            print("\n🤔 Thinking...")
            result = qa_system.ask(question)
            
            print(f"\n📝 Answer:")
            print("-" * 80)
            print(result['answer'])
            print("-" * 80)
            
            # Show sources
            if result['sources']:
                print(f"\n📚 Sources:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"  {i}. {source.get('title', 'Unknown')}")
                    if source.get('source'):
                        print(f"     {source['source']}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()