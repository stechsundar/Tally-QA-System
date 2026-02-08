"""
qa_system.py - LangChain RAG system for Tally Q&A
Run this SECOND to create the vector store from scraped data
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import PyPDFLoader
import json
import os
from dotenv import load_dotenv

class TallyQASystem:
    def __init__(self, docs_file='tally_docs.json', persist_directory='./tally_chroma_db'):
        self.persist_directory = persist_directory
        self.docs_file = docs_file
        self.vectorstore = None
        self.qa_chain = None
        self.chat_history = []
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
    def load_documents(self):
        """Load documents from JSON file"""
        if not os.path.exists(self.docs_file):
            raise FileNotFoundError(f"{self.docs_file} not found. Run scraper.py first!")
        
        with open(self.docs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to LangChain Document format
        documents = []
        for item in data:
            doc = Document(
                page_content=item['content'],
                metadata={
                    'source': item['url'],
                    'title': item['title'],
                    'category': item.get('category', '')
                }
            )
            documents.append(doc)
        
        print(f"✓ Loaded {len(documents)} documents")
        return documents
    
    def create_vectorstore(self):
        """Create and persist vector store"""
        print("\n" + "="*80)
        print("Creating Vector Store")
        print("="*80)
        
        # Load documents
        print("\n1. Loading documents...")
        documents = self.load_documents()
        
        # Split documents into chunks
        print("2. Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        print(f"✓ Split into {len(splits)} chunks")
        
        # Create vector store
        print("3. Creating embeddings and vector store...")
        print("   (This may take a few minutes...)")
        
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Vector store created and saved to {self.persist_directory}")
        return self.vectorstore
    
    def load_vectorstore(self):
        """Load existing vector store"""
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError(
                f"Vector store not found at {self.persist_directory}. "
                "Create it first using create_vectorstore()"
            )
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
        print(f"✓ Vector store loaded from {self.persist_directory}")
        return self.vectorstore
    
    def create_qa_chain(self, anthropic_api_key):
        """Create the QA chain"""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized!")
        
        # Initialize Claude
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=anthropic_api_key,
            max_tokens=2000,
            temperature=0
        )
        
        # Create retriever with broader search
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 20, "fetch_k": 60}
        )
        
        # Create prompt template
        template = """You are a helpful Tally expert assistant. Use the following pieces of context from Tally documentation to answer the question at the end.

If you don't know the answer based on the context provided, just say that you don't know, don't try to make up an answer.

If the question is about how to do something in Tally, provide step-by-step instructions when possible.

Context:
{context}

Question: {question}

Helpful Answer:"""
        
        prompt = PromptTemplate.from_template(template)
        
        # Format documents function with source prioritization
        self.format_docs_node = self._format_docs
        
        # Create chain
        self.qa_chain = (
            {"context": retriever | self._format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Store components for hybrid access
        self.prompt = prompt
        self.llm = llm
        self.retriever = retriever
        
        # Original chain for backward compatibility
        self.qa_chain = (
            {"context": retriever | self._format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
    
    def _format_docs(self, docs):
        """Sort docs to put PDFs first (Knowledge Boost)"""
        pdfs = [d for d in docs if d.metadata.get('source', '').lower().endswith('.pdf')]
        others = [d for d in docs if not d.metadata.get('source', '').lower().endswith('.pdf')]
        
        sorted_docs = pdfs + others
        return "\n\n".join(f"[{doc.metadata.get('title', 'Doc')}]: {doc.page_content}" for doc in sorted_docs)

    def ask(self, question):
        """Ask a question with Hybrid/Ensemble Retrieval"""
        if self.qa_chain is None:
            raise ValueError("QA chain not initialized!")
        
        # 1. Ultra-Deep Search + Metadata Filtering
        # We try to get the best matches globally AND specifically from PDFs
        try:
             # Global search
             global_docs = self.vectorstore.similarity_search(question, k=50)
             
             # Targeted PDF Search (Chroma where filter)
             # Note: Using absolute path pattern or simple match if possible
             # But since we saw they are in 'pdf_docs/', we'll use a larger scan and filter
             pdf_docs = [d for d in self.vectorstore.similarity_search(question, k=200) 
                         if d.metadata.get('source', '').lower().endswith('.pdf')]
             
             # Combined pool
             combined_pool = pdf_docs + global_docs
        except:
             combined_pool = self.vectorstore.similarity_search(question, k=50)
        
        # De-duplicate and prioritize PDFs
        final_docs = []
        seen_chunks = set()
        
        # Priority 1: PDFs
        for d in combined_pool:
            if d.metadata.get('source', '').lower().endswith('.pdf'):
                if d.page_content[:200] not in seen_chunks:
                    final_docs.append(d)
                    seen_chunks.add(d.page_content[:200])
        
        # Priority 2: Standard docs (until we hit 15-20 docs)
        for d in combined_pool:
            if not d.metadata.get('source', '').lower().endswith('.pdf'):
                if d.page_content[:200] not in seen_chunks:
                    final_docs.append(d)
                    seen_chunks.add(d.page_content[:200])
                    if len(final_docs) >= 20: break
                    
        # Limit context
        context_docs = final_docs[:15]
        context_text = self._format_docs(context_docs)
        
        # 3. Targeted LLM Call
        from langchain_core.output_parsers import StrOutputParser
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context_text, "question": question})
        
        return {
            'answer': answer,
            'sources': [doc.metadata for doc in final_docs[:5]]
        }

    def add_pdf(self, pdf_path):
        """Load a PDF and add it to the vector store"""
        print(f"\nProcessing PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata['source'] = pdf_path
            doc.metadata['title'] = os.path.basename(pdf_path)
            
        # Split
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        # Add to existing vector store
        if self.vectorstore is None:
            self.load_vectorstore()
            
        self.vectorstore.add_documents(splits)
        print(f"✓ Added {len(splits)} chunks from {pdf_path} to vector store")
        return len(splits)

    def batch_add_pdfs(self, directory='pdf_docs'):
        """Batch add all PDFs from a directory"""
        if not os.path.exists(directory):
            print(f"Directory {directory} not found.")
            return
        
        pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"No PDF files found in {directory}.")
            return
            
        print(f"\n" + "="*80)
        print(f"Batch Processing {len(pdf_files)} PDFs")
        print("="*80)
        
        total_chunks = 0
        for pdf_file in pdf_files:
            pdf_path = os.path.join(directory, pdf_file)
            try:
                chunks = self.add_pdf(pdf_path)
                total_chunks += chunks
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
        
        print(f"\n✓ Finished batch processing. Added total of {total_chunks} chunks.")

def main():
    """Create vector store - run this once after scraping"""
    # Load environment variables
    load_dotenv()
    
    print("="*80)
    print("Tally QA System - Vector Store Setup")
    print("="*80)
    
    # Check if tally_docs.json exists
    if not os.path.exists('tally_docs.json'):
        print("\n❌ Error: tally_docs.json not found!")
        print("Please run 'python scraper.py' first to scrape Tally documentation.")
        return
    
    # Check if vector store already exists
    if os.path.exists('./tally_chroma_db'):
        response = input("\nVector store already exists. Recreate it? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Skipping vector store creation.")
            print("Run 'python main.py' to start asking questions.")
            return
    
    # Create vector store
    qa_system = TallyQASystem()
    qa_system.create_vectorstore()
    
    print("\n" + "="*80)
    print("✓ Setup Complete!")
    print("="*80)
    print("\nNext step: Run 'python main.py' to start asking questions about Tally.")

if __name__ == "__main__":
    main()