import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

print("🔄 Loading existing vector store...")

persist_directory = "./tally_chroma_db"

# Create embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load existing vectorstore (if exists)
if os.path.exists(persist_directory):
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    print("✅ Existing vector store loaded")
else:
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    print("🆕 New vector store will be created")

# Get existing URLs
existing_data = vectorstore.get()
existing_urls = set()

if existing_data and "metadatas" in existing_data:
    for metadata in existing_data["metadatas"]:
        if metadata and "source" in metadata:
            existing_urls.add(metadata["source"])

print(f"📌 Existing URLs in DB: {len(existing_urls)}")

# Load new JSON
with open("tally_docs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

new_documents = []

for item in data:
    if item["url"] not in existing_urls:
        new_documents.append(
            Document(
                page_content=item["content"],
                metadata={
                    "source": item["url"],
                    "title": item["title"],
                    "category": item.get("category", "")
                },
            )
        )

print(f"🆕 New URLs to add: {len(new_documents)}")

if new_documents:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    batch_size = 20
    total_docs = len(new_documents)

    print("🚀 Starting incremental update...")

    for i in range(0, total_docs, batch_size):
        batch_docs = new_documents[i:i+batch_size]
        splits = text_splitter.split_documents(batch_docs)

        vectorstore.add_documents(splits)

        print(f"✅ Processed {i + len(batch_docs)} / {total_docs} documents")

    print("🎯 All new documents added successfully!")

else:
    print("⚠️ No new documents to add.")
