import streamlit as st
import os
from dotenv import load_dotenv
from qa_system import TallyQASystem
from analytics_engine import TallyAnalyticsEngine
import time
import tempfile

# --- Page Config ---
st.set_page_config(
    page_title="Tally Expert AI Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    .main-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px 8px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.2);
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    .status-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def get_systems():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, None, "Error: ANTHROPIC_API_KEY not found in .env"
    
    try:
        qa_system = TallyQASystem()
        qa_system.load_vectorstore()
        qa_system.create_qa_chain(api_key)
        
        analytics_engine = TallyAnalyticsEngine()
        
        return qa_system, analytics_engine, None
    except Exception as e:
        return None, None, f"Error initializing systems: {str(e)}"

# --- UI Functions ---
def show_sidebar(qa_system, analytics_engine):
    with st.sidebar:
        st.image("https://www.tallysolutions.com/wp-content/uploads/2021/08/tally-logo.png", width=150)
        st.markdown("### 🎛️ Control Panel")
        
        st.markdown("### 💾 Data Source")
        uploaded_csv = st.file_uploader("Upload Tally CSV Export", type="csv", key="data_uploader")
        if uploaded_csv:
            success, msg = analytics_engine.load_csv(uploaded_csv)
            if success:
                st.success(f"✅ Data Active: {msg}")
            else:
                st.error(msg)
        
        st.markdown("---")
        st.markdown("### 🌐 Live URL Ingest")
        ingest_url = st.text_input("Paste Tally Help URL", placeholder="https://help.tallysolutions.com/...")
        if st.button("🚀 Ingest & Learn", use_container_width=True):
            if ingest_url:
                with st.spinner("Scraping and indexing..."):
                    try:
                        chunks = qa_system.add_url(ingest_url)
                        if chunks > 0:
                            st.success(f"✅ Learned! Added {chunks} new knowledge chunks.")
                            # Refresh vectorstore in the background
                            qa_system.load_vectorstore()
                        else:
                            st.error("Failed to extract content. Please check the URL.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a URL first.")

        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.kb_messages = []
            st.session_state.data_messages = []
            st.rerun()
            
        if st.button("🔄 Reload AI Engine", use_container_width=True):
            st.cache_resource.clear()
            st.success("AI Engine reloaded!")
            st.rerun()

# --- Main App ---
def main():
    st.markdown('<div class="main-header"><h1>🎯 Tally Expert AI</h1></div>', unsafe_allow_html=True)
    
    qa_system, analytics_engine, error = get_systems()
    show_sidebar(qa_system, analytics_engine)
    
    if error:
        st.error(error)
        return

    tab1, tab2 = st.tabs(["📚 Knowledge Base", "📊 Data Analytics"])

    with tab1:
        st.markdown("### Ask about Tally Features & Processes")
        # Initialize history for KB
        if "kb_messages" not in st.session_state:
            st.session_state.kb_messages = []

        # Display history
        for msg in st.session_state.kb_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("How do I enable BOM in TallyPrime?", key="kb_input"):
            st.session_state.kb_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                # Use a placeholder for the status
                status_placeholder = st.empty()
                with status_placeholder:
                    with st.spinner("Consulting local knowledge..."):
                         # The qa_system.ask() now handles discover_and_ingest internally
                         result = qa_system.ask(prompt)
                
                ans = result['answer']
                st.markdown(ans)
                if result['sources']:
                    # Only show Web URLs that were actually cited in the answer
                    import re
                    cited_sources = re.findall(r'\[Source (\d+)\]', ans)
                    cited_indices = [int(i)-1 for i in cited_sources]
                    
                    web_sources_to_show = []
                    seen_urls = set()
                    
                    for i, s in enumerate(result['sources']):
                        source_url = s.get('source', '')
                        # Show if cited OR if it's one of the top 3 relevant web results
                        if (i in cited_indices or i < 3) and not source_url.lower().endswith('.pdf'):
                            if source_url and source_url not in seen_urls:
                                web_sources_to_show.append(s)
                                seen_urls.add(source_url)
                    
                    if web_sources_to_show:
                        with st.expander("🌐 Official Tally Documentation Links"):
                            for s in web_sources_to_show:
                                st.markdown(f"- [{s.get('title', 'Tally Help Page')}]({s.get('source')})")
                st.session_state.kb_messages.append({"role": "assistant", "content": ans})

    with tab2:
        st.markdown("### Query your Tally Data (CSV)")
        if analytics_engine.df is None:
            st.info("💡 Please upload a CSV file in the sidebar to start data analysis.")
            st.markdown("""
            **Example questions you can ask once data is uploaded:**
            - What is the total revenue for the last quarter?
            - Which items have the lowest stock levels?
            - List the top 5 customers by voucher value.
            """)
        else:
            summary = analytics_engine.get_summary()
            st.markdown(f"**Loaded:** {summary['rows']} rows | **Columns:** {', '.join(summary['columns'])}")
            with st.expander("👀 Data Preview"):
                st.dataframe(summary['preview'], use_container_width=True)

            if "data_messages" not in st.session_state:
                st.session_state.data_messages = []

            for msg in st.session_state.data_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if data_prompt := st.chat_input("Show me a summary of sales by ledger", key="data_input"):
                st.session_state.data_messages.append({"role": "user", "content": data_prompt})
                with st.chat_message("user"):
                    st.markdown(data_prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing data..."):
                        ans = analytics_engine.ask(data_prompt)
                        st.markdown(ans)
                        st.session_state.data_messages.append({"role": "assistant", "content": ans})

if __name__ == "__main__":
    main()
