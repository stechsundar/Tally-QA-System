"""
qa_system.py - LangChain RAG system for Tally Q&A
"""

import os
import json

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
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        self.vectorstore = Chroma.from_documents(
            splits, self.embeddings, persist_directory=self.persist_directory,
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
            model="claude-3-haiku-20240307",
            anthropic_api_key=anthropic_api_key,
            temperature=0,
            max_tokens=1500,
        )

        template = """You are a TallyPrime documentation assistant.

Answer using ONLY the provided context. Do not invent steps. Do not repeat information.

For procedural questions (how to, steps, configure, setup):
- Give numbered step-by-step instructions
- Include exact navigation paths (e.g., Gateway of Tally > Vouchers > F4)
- Include keyboard shortcuts
- Be practical, not descriptive

For conceptual questions:
- Give structured explanation with headings

Context:
{context}

Question:
{question}

Respond in this exact format below. Do not include any labels or sections other than these two:

SHORT_ANSWER:
[2-3 line concise summary only]

LONG_ANSWER:
[Detailed step-by-step explanation with **bold** navigation paths]"""

        self.prompt = PromptTemplate.from_template(template)

    # ------------------ YOUTUBE VIDEO MATCHING ------------------

    # Words too generic to be useful keywords (appear in almost every Tally video)
    STOP_WORDS = {
        "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
        "is", "it", "how", "what", "when", "where", "why", "do", "does", "can",
        "i", "my", "me", "with", "from", "that", "this", "set", "use", "get",
        "show", "tell", "please", "using", "by", "up", "into", "via", "will",
        "should", "would", "could", "about", "also", "than", "then", "its",
        "tally", "tallyprime", "prime", "step", "tutorial", "tamil",
    }

    def find_matching_videos(self, question, max_results=3):
        """
        Simplified high-reliability title matching for a small video set.
        """
        if self.vectorstore is None:
            return []

        # 1. Fetch ALL YouTube videos from the DB (since there are only 10)
        # k=100 ensures we grab every single video in the category
        try:
            all_yt_docs = self.vectorstore.similarity_search(
                "", k=100, filter={"category": "youtube"}
            )
        except Exception:
            # Fallback if filter is picky
            all_yt_docs = self.vectorstore.similarity_search("tally", k=100)
            all_yt_docs = [d for d in all_yt_docs if d.metadata.get("category") == "youtube"]

        # 2. Extract keywords from user question
        import re
        clean_q = re.sub(r'[^\w\s]', '', question.lower())
        keywords = [w for w in clean_q.split() if len(w) > 2 and w not in self.STOP_WORDS]
        
        # If no keywords left (e.g. "how to do it"), return nothing to avoid random videos
        if not keywords:
            return []

        scored_results = []
        seen_urls = set()

        # 3. Manual Title Check (The 'Reliability' Engine)
        for doc in all_yt_docs:
            url = doc.metadata.get("source", "")
            if not url or url in seen_urls:
                continue
                
            title = doc.metadata.get("title", "").lower()
            
            # Count how many user keywords appear in this specific video title
            match_count = sum(1 for kw in keywords if kw in title)
            
            if match_count > 0:
                # Calculate a simple score
                # Bonus: if the keyword "backup" is in the title and user asked for "backup"
                score = match_count * 10 
                
                scored_results.append({
                    "source": url,
                    "title": doc.metadata.get("title", ""),
                    "channel": doc.metadata.get("channel", ""),
                    "score": score
                })
                seen_urls.add(url)

        # 4. Sort by highest match first
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        print(f"DEBUG: Found {len(scored_results)} title matches for keywords {keywords}")
        return scored_results[:max_results]        

    def find_matching_videos_old(self, question, max_results=3):
        """
        Find YouTube videos relevant to the question using keyword title matching.

        WHY NOT similarity_search_with_relevance_scores:
          ChromaDB + HuggingFace embeddings returns broken relevance scores
          (negative values like -0.12, 0.015) due to cosine->L2 conversion.
          These cannot be used for thresholding.

        Strategy A (primary): Extract meaningful words from the question,
          count how many appear in each video title. Sort by hit count.
          "Schedule Backup TallyDrive" -> "AUTO BACKUP | TALLY PRIME 7.0" (2 hits)

        Strategy B (fallback): If no keyword matches, return top-ranked YouTube
          docs by semantic order (ChromaDB best-first is reliable even without scores).
        """
        if self.vectorstore is None:
            return []

        # Fetch YouTube docs pool
        try:
            yt_docs = self.vectorstore.similarity_search(
                question, k=50, filter={"category": "youtube"},
            )
            print(f"YouTube pool: {len(yt_docs)} chunks")
        except Exception as e:
            print(f"Filtered search failed ({e}), trying unfiltered...")
            try:
                all_docs = self.vectorstore.similarity_search(question, k=100)
                yt_docs = [d for d in all_docs if d.metadata.get("category") == "youtube"]
                print(f"Fallback: {len(yt_docs)} YouTube chunks")
            except Exception as e2:
                print(f"Both searches failed: {e2}")
                return []

        if not yt_docs:
            print("No YouTube docs in ChromaDB")
            return []

        # Extract meaningful keywords from question
        keywords = [
            w.lower() for w in question.replace("-", " ").split()
            if len(w) > 2 and w.lower() not in self.STOP_WORDS
        ]
        print(f"Keywords: {keywords}")

        # Strategy A: keyword match against video title
        seen_urls = set()
        scored = []

        for doc in yt_docs:
            url = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title_lower = title.lower()
            hits = [kw for kw in keywords if kw in title_lower]
            if hits:
                scored.append({
                    "source": url,
                    "title": title,
                    "channel": doc.metadata.get("channel", ""),
                    "hits": len(hits),
                })
                print(f"  Keyword match [{len(hits)}]: {title[:60]}")

        scored.sort(key=lambda x: x["hits"], reverse=True)
        final = scored[:max_results]

        # Strategy B: semantic fallback
        if not final:
            print("No keyword matches, using semantic top-K fallback")
            seen_fb = set()
            for doc in yt_docs:
                url = doc.metadata.get("source", "")
                if not url or url in seen_fb:
                    continue
                seen_fb.add(url)
                final.append({
                    "source": url,
                    "title": doc.metadata.get("title", ""),
                    "channel": doc.metadata.get("channel", ""),
                })
                print(f"  Fallback: {doc.metadata.get('title','')[:60]}")
                if len(final) >= max_results:
                    break

        result = [
            {"source": v["source"], "title": v["title"], "channel": v["channel"]}
            for v in final
        ]
        print(f"Final video matches: {len(result)}")
        for v in result:
            print(f"  -> {v['title'][:65]}")
        return result


    def find_tally_videos(self, sources):
        """
        Extract official Tally video links from the documentation sources
        already retrieved for the answer.

        Tally's help site (help.tallysolutions.com) embeds video links
        directly in the source URLs or as related pages. We detect them
        by checking if the source URL contains known Tally video patterns.

        Returns a list of dicts: [{source, title}]
        """
        tally_video_links = []
        seen = set()

        for s in sources:
            url = s.get("source", "")
            title = s.get("title", "")

            if not url or url in seen:
                continue

            # Tally's video content is hosted on their help site or YouTube
            # under the official Tally channel
            is_tally_video = (
                "tallysolutions.com" in url and "video" in url.lower()
            ) or (
                "youtube.com" in url and "tally" in title.lower()
                and "techsoft" not in url  # exclude TSS videos
            ) or (
                "help.tallysolutions.com" in url and any(
                    kw in url.lower() for kw in ["video", "watch", "tutorial"]
                )
            )

            if is_tally_video:
                seen.add(url)
                tally_video_links.append({"source": url, "title": title})
                if len(tally_video_links) >= 1:  # show max 1 Tally video
                    break

        return tally_video_links



    def ask(self, question):
        if not self.prompt or not self.llm:
            raise ValueError("QA chain not initialized")

        try:
            # Get docs, exclude YouTube from LLM context
            docs = self.vectorstore.similarity_search(question, k=15)
            doc_context = [d for d in docs if d.metadata.get("category") != "youtube"]
            context = self._format_docs(doc_context)

            # Generate answer
            chain = self.prompt | self.llm | StrOutputParser()
            raw = chain.invoke({"context": context, "question": question})
            print(f"LLM raw response length: {len(raw)}")

            # Parse SHORT / LONG
            if "SHORT_ANSWER:" in raw and "LONG_ANSWER:" in raw:
                short = raw.split("SHORT_ANSWER:")[1].split("LONG_ANSWER:")[0].strip()
                long  = raw.split("LONG_ANSWER:")[1].strip()
            else:
                short = raw[:300]
                long  = raw

            # Documentation sources only
            sources = [
                {"title": d.metadata.get("title", ""), "source": d.metadata.get("source", "")}
                for d in doc_context
                if not d.metadata.get("source", "").startswith("https://www.youtube.com")
            ]

            # TSS YouTube videos (techsoft subdomain only on frontend)
            try:
                video_links = self.find_matching_videos(question, max_results=3)
            except Exception as e:
                print(f"WARNING: find_matching_videos failed: {e}")
                video_links = []

            # Official Tally videos from sources
            try:
                tally_video_links = self.find_tally_videos(sources)
            except Exception as e:
                print(f"WARNING: find_tally_videos failed: {e}")
                tally_video_links = []

            return {
                "short_answer":      short,
                "long_answer":       long,
                "sources":           sources,
                "watch_video":       len(video_links) > 0,
                "video_links":       video_links,
                "tally_video_links": tally_video_links,
            }

        except Exception as e:
            import traceback
            print(f"ERROR in ask(): {e}")
            traceback.print_exc()
            raise

    # ------------------ UTILS ------------------

    def _format_docs(self, docs):
        return "\n\n".join(
            f"[{d.metadata.get('title', 'Doc')}]\n{d.page_content}"
            for d in docs
        )