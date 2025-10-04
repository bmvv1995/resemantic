"""
Session management utilities for Streamlit.
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import List, Dict


def init_session_state():
    """Initialize session state variables."""

    # Conversation ID
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())

    # Messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Semantic data
    if 'semantic_units' not in st.session_state:
        st.session_state.semantic_units = []

    if 'propositions' not in st.session_state:
        st.session_state.propositions = []

    # Processing state
    if 'processing' not in st.session_state:
        st.session_state.processing = False


def add_message(role: str, content: str) -> Dict:
    """Add a message to the conversation."""

    message = {
        'id': str(uuid.uuid4()),
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }

    st.session_state.messages.append(message)
    return message


def get_conversation_context(window: int = 3) -> str:
    """Get recent conversation context."""

    if len(st.session_state.messages) == 0:
        return "Start of conversation"

    recent = st.session_state.messages[-window:]
    return "\n".join([
        f"{msg['role']}: {msg['content'][:200]}..."
        for msg in recent
    ])


def clear_conversation():
    """Clear current conversation and start fresh."""

    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.semantic_units = []
    st.session_state.propositions = []
    st.session_state.processing = False


def get_stats() -> Dict:
    """Get conversation statistics."""

    return {
        'conversation_id': st.session_state.conversation_id,
        'total_messages': len(st.session_state.messages),
        'user_messages': len([m for m in st.session_state.messages if m['role'] == 'user']),
        'assistant_messages': len([m for m in st.session_state.messages if m['role'] == 'assistant']),
        'semantic_units': len(st.session_state.semantic_units),
        'propositions': len(st.session_state.propositions),
        'avg_props_per_message': len(st.session_state.propositions) / len(st.session_state.messages) if st.session_state.messages else 0
    }
