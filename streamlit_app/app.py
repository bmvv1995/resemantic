"""
ReSemantic - Conversational AI with Living Knowledge
Main Streamlit application
"""

import streamlit as st
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="ReSemantic",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",  # Auto-collapse on mobile
    menu_items={
        'About': "ReSemantic - Proposition-based conversational memory"
    }
)

# Custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem 0.5rem;
        }
        .stButton > button {
            width: 100%;
            margin: 0.25rem 0;
        }
        .stMarkdown {
            font-size: 0.9rem;
        }
        section[data-testid="stSidebar"] {
            width: 0px;
        }
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Better spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Main page
st.title("🧠 ReSemantic")
st.markdown("**Conversational AI with Living Knowledge**")
st.markdown("---")

# Info
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💬 Chat")
    st.markdown("Engage in conversation with semantic memory extraction")
    if st.button("Go to Chat", type="primary", use_container_width=True):
        st.switch_page("pages/1_💬_Chat.py")

with col2:
    st.markdown("### 📊 Dashboard")
    st.markdown("View analytics and semantic insights")
    if st.button("Go to Dashboard", use_container_width=True):
        st.switch_page("pages/2_📊_Dashboard.py")

st.markdown("---")

# System info
with st.expander("ℹ️ About ReSemantic"):
    st.markdown("""
    **ReSemantic** transforms conversations into atomic propositions:

    - 🎯 **Stage 1**: Extract semantic units with rich metadata
    - ⚛️ **Stage 2**: Break into atomic propositions
    - 🧠 **Memory**: Store in knowledge graph (Neo4j)
    - 🔍 **Retrieval**: Vector + semantic search

    **Technology:**
    - Two-stage semantic extraction (FIXED pipeline)
    - Proposition-based memory (no hallucinations)
    - Mobile-responsive interface
    """)

# Status
if os.getenv("OPENAI_API_KEY"):
    st.success("✅ OpenAI API configured")
else:
    st.error("❌ OpenAI API key not found - set OPENAI_API_KEY in .env")
