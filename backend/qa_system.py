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

        self.prompt = PromptTemplate.from_template("""
            You are a professional TallyPrime documentation assistant.

            Strict Instructions:

            1. If the question is procedural (how to, detailed, steps, process, configure, setup, create):
            - Provide clear step-by-step instructions.
            - Include exact navigation paths (e.g., Gateway of Tally > Vouchers > Ctrl+F4 (Payroll)).
            - Include keyboard shortcuts.
            - Use numbered steps.
            - Be practical, not descriptive.
            - Avoid marketing language.
            - Avoid generic feature explanations.

            2. If the question is conceptual:
            - Provide structured explanation with headings.

            3. Use only information from the provided context.
            4. Do not invent steps.
            5. Do not give high-level summaries when detailed steps are possible.
            Do not repeat the same information.
            Do not restate identical steps.
            Avoid duplication.

            Format:

            SHORT_ANSWER:
            (Concise summary in 2–3 lines)
            (Avoid long answer content here)
            LONG_ANSWER:
            (Detailed step-by-step explanation if applicable)

            Context:
            {context}

            Question:
            {question}
            """)


        print("✅ QA chain initialized successfully.")

    def _rewrite_query(self, question):
        q = question.lower()

        if "gst" in q:
            return question + " GST configuration compliance returns GSTR-1 GSTR-3B"
        
        if "security" in q or "permission" in q:
            return question + " user roles security levels access rights"

        if "inventory" in q or "stock" in q:
            return question + " stock item inventory management reorder level"

        if "reorder" in q:
            return "how to reorder stock item reorder level minimum order quantity"

        return question  # ✅ ALWAYS return something

    # ------------------ ASK ------------------
    def _hybrid_retrieve(self, question, k=20):
        try:
            keyword_docs = self.vectorstore.similarity_search(
                question,
                k=k
            )

            retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k}
            )
            mmr_docs = retriever.invoke(question)

            combined = keyword_docs + mmr_docs

            unique = {}
            for d in combined:
                key = (d.metadata.get("source", ""), d.page_content[:100])
                if key not in unique:
                    unique[key] = d

            return list(unique.values())[:k]

        except Exception as e:
            print("🔥 hybrid_retrieve ERROR:", str(e))
            return []   # 🔥 ALWAYS RETURN SAFE VALUE

    def ask(self, question):
        docs = []

        try:
            if not self.vectorstore:
                raise ValueError("Vectorstore not loaded")

            if not self.prompt or not self.llm:
                raise ValueError("QA chain not initialized")

            # ------------------ QUERY REWRITE ------------------
            rewritten_question = self._rewrite_query(question)
            q = rewritten_question.lower()

            # ------------------ DYNAMIC RETRIEVAL DEPTH ------------------
            k = 15
            if "complete" in q or "full" in q:
                k = 30
            if any(x in q for x in ["gst", "gstr", "tax", "rcm"]):
                k = 35
            if any(x in q for x in ["security", "user", "permission"]):
                k = 30
            if any(x in q for x in ["inventory", "stock", "reorder"]):
                k = 30

            # ------------------ HYBRID RETRIEVAL ------------------
            docs = self._hybrid_retrieve(rewritten_question, k=k)

            if not docs:
                return {
                    "short_answer": "No relevant documentation found.",
                    "long_answer": "The system could not retrieve relevant TallyPrime documentation for this topic.",
                    "sources": [],
                    "watch_video": False,
                    "video_links": []
                }

            # ------------------ GENERATION ------------------
            context = self._format_docs(docs)
            chain = self.prompt | self.llm | StrOutputParser()

            raw_response = chain.invoke({
                "context": context,
                "question": question
            })

            # ------------------ PARSE RESPONSE ------------------
            if "SHORT_ANSWER:" in raw_response and "LONG_ANSWER:" in raw_response:
                short = raw_response.split("SHORT_ANSWER:")[1].split("LONG_ANSWER:")[0].strip()
                long = raw_response.split("LONG_ANSWER:")[1].strip()
            else:
                short = raw_response[:300]
                long = raw_response

            # ------------------ SAFE SOURCE BUILD ------------------
            related_articles = []
            seen = set()

            for d in docs:
                source = d.metadata.get("source", "")
                title = d.metadata.get("title", "Unknown")

                if not source:
                    continue
                # 🔥 NORMALIZE URL (remove fragments + query params)
                clean_source = source.split("#")[0].split("?")[0].strip().lower()

                if clean_source not in seen:
                    related_articles.append({
                        "title": title,
                        "source": clean_source
                    })
                    seen.add(clean_source)
            # ------------------ VIDEO DETECTION ------------------
            watch_video = False
            video_links = []

            for article in related_articles:
                src = article["source"].lower()

                # Detect video pages automatically
                if "video" in src or "youtube.com" in src or "youtu.be" in src:
                    watch_video = True
                    video_links.append({
                        "title": article["title"],
                        "source": article["source"]
                    })

            # ------------------ FINAL RETURN ------------------
            return {
                "short_answer": short,
                "long_answer": long,
                "sources": related_articles[:5],
                "watch_video": watch_video,
                "video_links": video_links
            }

        except Exception as e:
            print("🔥 ask() ERROR:", str(e))
            return {
                "short_answer": "An internal error occurred.",
                "long_answer": str(e),
                "sources": [],
                "watch_video": False,
                "video_links": []
            }

    # ------------------ FORMAT DOCS ------------------

    def _format_docs(self, docs):
        return "\n\n".join(
            f"Title: {doc.metadata.get('title')}\n"
            f"Source: {doc.metadata.get('source')}\n"
            f"{doc.page_content}"
            for doc in docs
        )
