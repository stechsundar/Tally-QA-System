"""
ingest_youtube.py - Fetch YouTube video titles & descriptions
and add them to the existing ChromaDB vector store.

Usage:
    pip install yt-dlp
    python ingest_youtube.py
"""

import yt_dlp
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ─── CONFIG ───────────────────────────────────────────────
YOUTUBE_CHANNELS = [
    "https://www.youtube.com/@techsoftsolutionstally",
    # Add more channel URLs here if needed
]

PERSIST_DIRECTORY = "./tally_chroma_db"  # Same as your existing ChromaDB
# ──────────────────────────────────────────────────────────


def fetch_channel_videos(channel_url: str) -> list[dict]:
    """Fetch all video titles and descriptions from a YouTube channel."""
    
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,       # Don't download, just get metadata
        "skip_download": True,
        "ignoreerrors": True,
    }

    videos = []

    print(f"\n📺 Fetching video list from: {channel_url}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get channel playlist info
        info = ydl.extract_info(f"{channel_url}/videos", download=False)

        if not info or "entries" not in info:
            print(f"⚠️  No videos found for {channel_url}")
            return []

        video_entries = info["entries"]
        print(f"   Found {len(video_entries)} videos. Fetching descriptions...")

    # Now fetch full info (including description) for each video
    ydl_opts_full = {
        "quiet": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
        for i, entry in enumerate(video_entries):
            if not entry:
                continue

            video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"

            try:
                video_info = ydl.extract_info(video_url, download=False)
                if not video_info:
                    continue

                title = video_info.get("title", "Untitled")
                description = video_info.get("description", "")
                video_id = video_info.get("id", "")

                # Skip if no useful content
                if not description.strip():
                    print(f"   [{i+1}/{len(video_entries)}] ⏭️  Skipping (no description): {title}")
                    continue

                videos.append({
                    "title": title,
                    "description": description,
                    "url": video_url,
                    "video_id": video_id,
                    "channel": channel_url,
                })

                print(f"   [{i+1}/{len(video_entries)}] ✅ {title[:60]}...")

            except Exception as e:
                print(f"   [{i+1}/{len(video_entries)}] ❌ Error: {e}")
                continue

    return videos


def videos_to_documents(videos: list[dict]) -> list[Document]:
    """Convert video metadata to LangChain Documents."""
    
    docs = []
    for video in videos:
        # Combine title + description as content (same pattern as your tally_docs.json)
        content = f"Video Title: {video['title']}\n\nDescription:\n{video['description']}"

        doc = Document(
            page_content=content,
            metadata={
                "source": video["url"],
                "title": video["title"],
                "category": "youtube",
                "channel": video["channel"],
                "video_id": video["video_id"],
            }
        )
        docs.append(doc)

    return docs


def add_to_chromadb(documents: list[Document]):
    """Add new documents to the existing ChromaDB vector store."""
    
    print(f"\n🔧 Loading existing ChromaDB from: {PERSIST_DIRECTORY}")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )

    # Split documents into chunks (same settings as qa_system.py)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    splits = splitter.split_documents(documents)
    print(f"📄 Split into {len(splits)} chunks from {len(documents)} videos")

    # Add to existing vectorstore
    print("⬆️  Adding to ChromaDB...")
    vectorstore.add_documents(splits)

    print(f"✅ Successfully added {len(splits)} chunks to ChromaDB!")
    print(f"   Total docs now: {vectorstore._collection.count()}")


def main():
    print("=" * 60)
    print("  YouTube Channel Ingestion for Tally QA System")
    print("=" * 60)

    all_videos = []

    for channel_url in YOUTUBE_CHANNELS:
        videos = fetch_channel_videos(channel_url)
        all_videos.extend(videos)

    if not all_videos:
        print("\n❌ No videos found. Check channel URLs and try again.")
        return

    print(f"\n📊 Total videos fetched: {len(all_videos)}")

    # Convert to LangChain documents
    documents = videos_to_documents(all_videos)

    # Add to ChromaDB
    add_to_chromadb(documents)

    print("\n🎉 Done! Now push your updated tally_chroma_db to Hugging Face Space.")
    print("   Run: git add backend/tally_chroma_db && git commit -m 'Add YouTube data' && git push")


if __name__ == "__main__":
    main()