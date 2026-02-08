from qa_system import TallyQASystem
import os

def ingest_now():
    print("🎯 Tally AI - PDF Ingestion Utility")
    print("-" * 40)
    
    qa = TallyQASystem()
    
    # Ensure vector store exists
    if not os.path.exists('./tally_chroma_db'):
        print("❌ Vector store not found. Initializing fresh...")
        from setup_pdf_only import setup_pdf_only
        setup_pdf_only()
        return

    qa.load_vectorstore()
    
    print("Checking for new PDFs in 'pdf_docs' folder...")
    qa.batch_add_pdfs('pdf_docs')
    
    print("\n✅ Update complete! Refresh your Streamlit app to see changes.")

if __name__ == "__main__":
    ingest_now()
