import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

PERSIST_DIR = "./tally_chroma_db"

def main():
    print("🚀 Creating Tally Chroma DB...\n")

    # Load JSON
    with open("tally_docs.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📄 Loaded documents: {len(data)}")

    # Convert to LangChain Documents
    docs = []
    for item in data:
        docs.append(
            Document(
                page_content=item["content"],
                metadata={
                    "source": item["url"],
                    "title": item["title"],
                },
            )
        )

    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    splits = splitter.split_documents(docs)

    print(f"🧩 Total chunks created: {len(splits)}")

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Remove old DB if exists
    if os.path.exists(PERSIST_DIR):
        print("🗑 Removing old DB...")
        import shutil
        shutil.rmtree(PERSIST_DIR)

    # Create Chroma DB
    vectorstore = Chroma.from_documents(
        splits,
        embeddings,
        persist_directory=PERSIST_DIR,
    )

    print("✅ Chroma DB created successfully!")

if __name__ == "__main__":
    main()
