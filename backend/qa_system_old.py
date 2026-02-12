import os
import json
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic


class TallyQASystem:

    def __init__(self):
        load_dotenv()

        self.docs_file = "tally_docs.json"
        self.persist_directory = "./tally_chroma_db"

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = None
        self.llm = None
        self.prompt = None

    # ------------------ VECTOR STORE ------------------

    def load_vectorstore(self):
        if not os.path.exists(self.persist_directory):
            raise FileNotFoundError("Chroma DB not found. Run create_vector_db.py first.")

        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

        print("✅ Vectorstore loaded successfully.")

    # ------------------ QA CHAIN ------------------

    def create_qa_chain(self):

        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
        )

        template = """
        You are a TallyPrime expert assistant.

        Use ONLY the provided context to answer the question.

        Use all relevant information from the provided context.
        If the information is spread across multiple sections,
        combine them into a comprehensive answer.
        Only say no information if nothing relevant is present at all.

        Context:
        {context}

        Question:
        {question}

        Respond strictly in this format:

        SHORT_ANSWER:
        <brief answer in 2-3 sentences>

        LONG_ANSWER:
        <detailed explanation>
        """

        self.prompt = PromptTemplate.from_template(template)

        print("✅ QA chain initialized successfully.")

    # ------------------ ASK ------------------

    def ask(self, question):
        try:
            if not self.vectorstore:
                raise ValueError("Vectorstore not loaded")

            if not self.prompt or not self.llm:
                raise ValueError("QA chain not initialized")

            # ------------------ RETRIEVAL ------------------

            if "complete" in question.lower() or "full" in question.lower():
                k = 30
                search_type = "similarity"
            else:
                k = 15
                search_type = "mmr"

            if "reorder" in question.lower() or "re-order" in question.lower():
                docs = self.vectorstore.similarity_search(
                    "reorder stock item reorder level",
                    k=k
                )
            else:
                retriever = self.vectorstore.as_retriever(
                    search_type=search_type,
                    search_kwargs={
                        "k": k
                    }
                )
                docs = retriever.invoke(question)

            if not docs:
                return {
                    "short_answer": "No relevant documents found.",
                    "long_answer": "The system could not retrieve relevant information.",
                    "sources": []
                }

            # ------------------ GENERATION ------------------

            context = self._format_docs(docs)

            chain = self.prompt | self.llm | StrOutputParser()

            raw_response = chain.invoke({
                "context": context,
                "question": question
            })

            if "SHORT_ANSWER:" in raw_response and "LONG_ANSWER:" in raw_response:
                short = raw_response.split("SHORT_ANSWER:")[1].split("LONG_ANSWER:")[0].strip()
                long = raw_response.split("LONG_ANSWER:")[1].strip()
            else:
                short = raw_response[:300]
                long = raw_response

            sources = [
                {
                    "title": d.metadata.get("title", "Unknown"),
                    "source": d.metadata.get("source", "")
                }
                for d in docs
            ]

            return {
                "short_answer": short,
                "long_answer": long,
                "sources": sources
            }

        except Exception as e:
            print("❌ ERROR IN ask():", str(e))
            raise


    # ------------------ FORMAT DOCS ------------------

    def _format_docs(self, docs):
        return "\n\n".join(
            f"Title: {doc.metadata.get('title')}\n"
            f"Source: {doc.metadata.get('source')}\n"
            f"{doc.page_content}"
            for doc in docs
        )
