"""
Chat interface page - mobile responsive
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Load environment variables from specific path
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import init_session_state, add_message, clear_conversation, get_conversation_context
from components.conversational_agent import ConversationalAgent
from components.semantic_extractor import SemanticExtractor

# Page config
st.set_page_config(
    page_title="Chat - ReSemantic",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile CSS
st.markdown("""
<style>
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main > div {
            padding: 0.5rem;
        }
        .stButton > button {
            width: 100%;
        }
    }

    /* Chat messages */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        max-width: 85%;
    }

    .user-message {
        background-color: #e3f2fd;
        margin-left: auto;
        text-align: right;
    }

    .assistant-message {
        background-color: #f5f5f5;
        margin-right: auto;
    }

    .message-role {
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
        opacity: 0.7;
    }

    /* Input area */
    .input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem;
        border-top: 1px solid #eee;
        z-index: 100;
    }

    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize
init_session_state()

# Initialize agents
if 'chat_agent' not in st.session_state:
    st.session_state.chat_agent = ConversationalAgent()

if 'semantic_extractor' not in st.session_state:
    st.session_state.semantic_extractor = SemanticExtractor()

# Header
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.button("🏠 Home"):
        st.switch_page("app.py")

with col2:
    st.title("💬 Chat")

with col3:
    if st.button("🗑️ Clear"):
        clear_conversation()
        st.rerun()

st.markdown("---")

# Chat display area
chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        st.info("👋 Start a conversation! Your messages will be semantically analyzed.")
    else:
        for msg in st.session_state.messages:
            role_class = "user-message" if msg['role'] == 'user' else "assistant-message"
            role_emoji = "👤" if msg['role'] == 'user' else "🤖"

            st.markdown(f"""
            <div class="chat-message {role_class}">
                <div class="message-role">{role_emoji} {msg['role'].title()}</div>
                <div>{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

# Background extraction processing
if 'extraction_queue' in st.session_state and st.session_state.extraction_queue:
    import threading

    def process_extraction():
        item = st.session_state.extraction_queue.pop(0)
        result = st.session_state.semantic_extractor.extract(
            message_content=item['message_content'],
            conversation_context=item['context'],
            role=item['role'],
            timestamp=item['timestamp'],
            message_id=item['message_id']
        )
        if result:
            st.session_state.semantic_units.append(result['semantic_unit'])
            st.session_state.propositions.extend(result['propositions'])

    # Start background thread
    thread = threading.Thread(target=process_extraction, daemon=True)
    thread.start()

    # Show discrete indicator
    st.caption("🧠 Processing semantic extraction in background...")

# Input area
st.markdown("---")

# Input form
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])

    with col1:
        user_input = st.text_input(
            "Your message",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )

    with col2:
        submit = st.form_submit_button(
            "Send",
            type="primary",
            use_container_width=True
        )

    if submit and user_input:
        # Add user message
        user_msg = add_message("user", user_input)

        # Get agent response
        with st.spinner("🤖 Thinking..."):
            response = st.session_state.chat_agent.chat(
                user_input,
                st.session_state.messages[:-1]  # Exclude the message we just added
            )

        # Add assistant message
        assistant_msg = add_message("assistant", response)

        # Queue extraction for background processing
        if 'extraction_queue' not in st.session_state:
            st.session_state.extraction_queue = []

        st.session_state.extraction_queue.append({
            'message_content': assistant_msg['content'],
            'context': get_conversation_context(window=5),
            'role': 'assistant',
            'timestamp': assistant_msg['timestamp'],
            'message_id': assistant_msg['id']
        })

        # Rerun to show new messages IMMEDIATELY
        st.rerun()

# Stats footer
if len(st.session_state.messages) > 0:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Messages", len(st.session_state.messages))

    with col2:
        st.metric("Semantic Units", len(st.session_state.semantic_units))

    with col3:
        st.metric("Propositions", len(st.session_state.propositions))
