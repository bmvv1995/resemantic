"""
Dashboard page - analytics and insights
"""

import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Load environment variables from specific path
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import init_session_state, get_stats

# Page config
st.set_page_config(
    page_title="Dashboard - ReSemantic",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile CSS
st.markdown("""
<style>
    @media (max-width: 768px) {
        .main > div {
            padding: 0.5rem;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: none !important;
        }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
init_session_state()

# Header
col1, col2 = st.columns([1, 5])

with col1:
    if st.button("🏠 Home"):
        st.switch_page("app.py")

with col2:
    st.title("📊 Dashboard")

st.markdown("---")

# Get stats
stats = get_stats()

# Main metrics
st.subheader("📈 Conversation Stats")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Messages", stats['total_messages'])

with col2:
    st.metric("Semantic Units", stats['semantic_units'])

with col3:
    st.metric("Propositions", stats['propositions'])

with col4:
    st.metric("Avg Props/Msg", f"{stats['avg_props_per_message']:.1f}")

st.markdown("---")

# Detailed breakdown
col1, col2 = st.columns(2)

with col1:
    st.subheader("💬 Messages Breakdown")

    if stats['total_messages'] > 0:
        st.metric("User Messages", stats['user_messages'])
        st.metric("Assistant Messages", stats['assistant_messages'])

        # Simple bar visualization
        user_pct = (stats['user_messages'] / stats['total_messages']) * 100
        assistant_pct = (stats['assistant_messages'] / stats['total_messages']) * 100

        st.progress(user_pct / 100, text=f"User: {user_pct:.0f}%")
        st.progress(assistant_pct / 100, text=f"Assistant: {assistant_pct:.0f}%")
    else:
        st.info("No messages yet. Start chatting!")

with col2:
    st.subheader("🎯 Semantic Analysis")

    if st.session_state.semantic_units:
        # Count narrative roles
        roles = {}
        for unit in st.session_state.semantic_units:
            role = unit.get('narrative_role', 'unknown')
            roles[role] = roles.get(role, 0) + 1

        total_units = len(st.session_state.semantic_units)

        for role, count in sorted(roles.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_units) * 100
            st.metric(f"{role.title()}", count)
            st.progress(pct / 100, text=f"{pct:.0f}%")
    else:
        st.info("No semantic analysis yet.")

st.markdown("---")

# Neo4j Graph Link
st.subheader("🕸️ Knowledge Graph")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    The knowledge graph visualization is available in Neo4j Browser.

    **Features:**
    - View proposition nodes
    - Explore temporal links (NEXT)
    - Discover semantic connections (SIMILAR_TO)
    - Query with Cypher
    """)

with col2:
    neo4j_url = "http://172.105.85.181:7474"

    st.link_button(
        "🔗 Open Neo4j Browser",
        neo4j_url,
        type="primary",
        use_container_width=True
    )

    st.caption("Username: neo4j")
    st.caption("Password: password123")

st.markdown("---")

# Recent semantic units
if st.session_state.semantic_units:
    st.subheader("🧠 Recent Semantic Units")

    # Show last 5
    for i, unit in enumerate(reversed(st.session_state.semantic_units[-5:])):
        with st.expander(f"Unit {len(st.session_state.semantic_units) - i}: {unit.get('type', 'unknown')} - {unit.get('narrative_role', 'unknown')}"):
            st.markdown(f"**Content:**")
            st.write(unit.get('content', 'N/A'))

            st.markdown(f"**Metadata:**")
            col1, col2 = st.columns(2)

            with col1:
                st.caption(f"Type: {unit.get('type', 'N/A')}")
                st.caption(f"Narrative Role: {unit.get('narrative_role', 'N/A')}")

            with col2:
                st.caption(f"Relevance: {unit.get('relevance', 'N/A')}")
                st.caption(f"Impact: {unit.get('impact', 'N/A')}")

            if unit.get('concepts'):
                st.caption(f"Concepts: {', '.join(unit.get('concepts', []))}")

# Recent propositions
if st.session_state.propositions:
    st.markdown("---")
    st.subheader("⚛️ Recent Propositions")

    # Show last 10
    for i, prop in enumerate(reversed(st.session_state.propositions[-10:])):
        with st.expander(f"Prop {len(st.session_state.propositions) - i}: [{prop.get('type', 'unknown')}] {prop.get('content', 'N/A')[:60]}..."):
            st.write(prop.get('content', 'N/A'))

            col1, col2 = st.columns(2)

            with col1:
                st.caption(f"Type: {prop.get('type', 'N/A')}")
                st.caption(f"Certainty: {prop.get('certainty', 'N/A')}")

            with col2:
                if prop.get('concepts'):
                    st.caption(f"Concepts: {', '.join(prop.get('concepts', []))}")

# Conversation ID
st.markdown("---")
st.caption(f"Conversation ID: {stats['conversation_id']}")
