"""
qa_system.py - LangChain RAG system for Tally Q&A
"""

import os
import json
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class TallyQASystem:
    def __init__(self, docs_file="tally_docs.json", persist_directory="./tally_chroma_db"):
        self.docs_file = docs_file
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.prompt = None
        self.llm = None

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    # ------------------ VECTOR STORE ------------------

    def load_documents(self):
        if not os.path.exists(self.docs_file):
            raise FileNotFoundError("Run scraper.py first")

        with open(self.docs_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [
            Document(
                page_content=item["content"],
                metadata={
                    "source": item["url"],
                    "title": item["title"],
                    "category": item.get("category", "")
                },
            )
            for item in data
        ]

    def create_vectorstore(self):
        docs = self.load_documents()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        splits = splitter.split_documents(docs)

        self.vectorstore = Chroma.from_documents(
            splits,
            self.embeddings,
            persist_directory=self.persist_directory,
        )

    def load_vectorstore(self):
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    # ------------------ QA CHAIN ------------------

    def create_qa_chain(self, anthropic_api_key):
        if self.vectorstore is None:
            raise ValueError("Vector store not loaded")

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=anthropic_api_key,
            temperature=0,
            max_tokens=1500,
        )

        template = """You are a Tally expert assistant.

Respond in this EXACT format:

SHORT_ANSWER:
A concise 2–3 line answer.

LONG_ANSWER:
A detailed explanation with steps and examples.
Use **bold** for Tally navigation paths.

RULES:
- Use ONLY the given context
- Do NOT mention sources inside answers

Context:
{context}

Question:
{question}
"""

        self.prompt = PromptTemplate.from_template(template)

    # ------------------ ASK ------------------

    def ask(self, question):
        if not self.prompt or not self.llm:
            raise ValueError("QA chain not initialized")

        docs = self.vectorstore.similarity_search(question, k=15)
        context = self._format_docs(docs)

        chain = self.prompt | self.llm | StrOutputParser()
        raw = chain.invoke({"context": context, "question": question})

        if "SHORT_ANSWER:" in raw and "LONG_ANSWER:" in raw:
            short = raw.split("SHORT_ANSWER:")[1].split("LONG_ANSWER:")[0].strip()
            long = raw.split("LONG_ANSWER:")[1].strip()
        else:
            short = raw[:300]
            long = raw

        sources = [
            {
                "title": d.metadata.get("title", "Unknown"),
                "source": d.metadata.get("source", ""),
            }
            for d in docs
        ]

        return {
            "short_answer": short,
            "long_answer": long,
            "sources": sources,
        }

    # ------------------ UTILS ------------------

    def _format_docs(self, docs):
        return "\n\n".join(
            f"[{d.metadata.get('title', 'Doc')}]\n{d.page_content}"
            for d in docs
        )
