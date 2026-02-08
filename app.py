import streamlit as st
import os
from dotenv import load_dotenv
from qa_system import TallyQASystem
import time

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
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .main-header h1 {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.5rem;
        margin: 0;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 1rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .stChatInputContainer {
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .source-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-top: 10px;
        font-size: 0.85rem;
    }
    
    .source-title {
        font-weight: 600;
        color: #3b82f6;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def get_qa_system():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "Error: ANTHROPIC_API_KEY not found in .env"
    
    try:
        qa_system = TallyQASystem()
        qa_system.load_vectorstore()
        qa_system.create_qa_chain(api_key)
        return qa_system, None
    except Exception as e:
        return None, f"Error initializing system: {str(e)}"

# --- UI Components ---
def show_header():
    st.markdown("""
        <div class="main-header">
            <h1>🎯 Tally Expert AI</h1>
            <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;">
                Your intelligent companion for all things Tally.ERP 9 and TallyPrime.
            </p>
        </div>
    """, unsafe_allow_html=True)

def show_sidebar(qa_system):
    with st.sidebar:
        st.image("https://www.tallysolutions.com/wp-content/uploads/2021/08/tally-logo.png", width=150)
        st.markdown("### System Status")
        if qa_system:
            st.success("✅ Engine Online")
            st.info("📚 Connected to Tally Knowledge Base")
        else:
            st.error("❌ Engine Offline")
        
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.write("• Ask about balance sheets, GST, or invoices.")
        st.write("• Be specific for better step-by-step guides.")
        st.write("• The AI learns from Tally documentation.")
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# --- Main Logic ---
def main():
    show_header()
    
    qa_system, error = get_qa_system()
    show_sidebar(qa_system)
    
    if error:
        st.error(error)
        st.info("Please ensure you've run the scraper and vector store setup steps first.")
        return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for src in message["sources"]:
                        st.markdown(f"""
                            <div class="source-card">
                                <div class="source-title">{src.get('title', 'Unknown')}</div>
                                <div style="color: #94a3b8;">{src.get('source', '')}</div>
                            </div>
                        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("How can I help you with Tally today?"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 *Thinking...*")
            
            try:
                result = qa_system.ask(prompt)
                full_response = result['answer']
                sources = result.get('sources', [])
                
                # Simulate typing effect
                typed_msg = ""
                for chunk in full_response.split():
                    typed_msg += chunk + " "
                    message_placeholder.markdown(typed_msg + "▌")
                    time.sleep(0.02)
                
                message_placeholder.markdown(full_response)
                
                if sources:
                    with st.expander("📚 Sources"):
                        for src in sources:
                            st.markdown(f"""
                                <div class="source-card">
                                    <div class="source-title">{src.get('title', 'Unknown')}</div>
                                    <div style="color: #94a3b8;">{src.get('source', '')}</div>
                                </div>
                            """, unsafe_allow_html=True)
                
                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

if __name__ == "__main__":
    main()
