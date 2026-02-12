import json
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load existing Chroma DB
vectorstore = Chroma(
    persist_directory="./tally_chroma_db",
    embedding_function=embeddings,
)


results = vectorstore.similarity_search("Complete GST configuration compliance", k=10)

for r in results:
    print(r.metadata["title"])
    print(r.metadata["source"])
    print("----")


""" with open("tally_docs.json", "r", encoding="utf-8") as f:
    docs = json.load(f)

for doc in docs:
    if "re-order" in doc["content"].lower():
        print(doc["title"])
        print(doc["url"])
        break
 """