#!/usr/bin/env python3
"""
ReSemantic CLI Chat - Conversational interface with BATCH semantic extraction
Uses batch_extraction graph for processing user + assistant messages together
"""

import os
import sys
import json
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.extraction_graph import graph
from config import ChatConfig

# Load environment
load_dotenv()

# Initialize chat model (with reasoning support if enabled)
if ChatConfig.ENABLE_REASONING_DISPLAY:
    chat_model = ChatAnthropic(
        model=ChatConfig.REASONING_MODEL,
        temperature=ChatConfig.CHAT_TEMPERATURE,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print(f"💭 REASONING MODE ENABLED (using {ChatConfig.REASONING_MODEL})")
else:
    chat_model = ChatAnthropic(
        model=ChatConfig.CHAT_MODEL,
        temperature=ChatConfig.CHAT_TEMPERATURE,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# Conversation history
conversation_history = []
message_counter = 0


def print_separator():
    print("\n" + "="*80 + "\n")


def print_extraction_summary(role, result):
    """Print extraction results WITH BLOCKS for one message in a readable format."""
    print(f"\n📊 SEMANTIC EXTRACTION ({role.upper()}):")
    print("-" * 80)

    # Semantic Unit
    su_key = f"{role}_semantic_unit"
    props_key = f"{role}_propositions"
    time_key1 = f"stage1_{role}_time"
    time_key2 = f"stage2_{role}_time"

    su = result.get(su_key, {})
    print(f"📝 Semantic Unit: {su.get('content', 'N/A')}")
    print(f"   Type: {su.get('type', 'N/A')} | Role: {su.get('narrative_role', 'N/A')}")
    print(f"   Concepts: {', '.join(su.get('concepts', []))}")
    
    # BLOCKS METADATA - NEW!
    block_meta = su.get('block_metadata', {})
    if block_meta:
        print(f"\n   🏷️  BLOCKS METADATA:")
        if block_meta.get('resource_url'):
            print(f"      📎 Resource: {block_meta['resource_url']}")
            if block_meta.get('resource_type'):
                print(f"         Type: {block_meta['resource_type']}")
        if block_meta.get('decision_choice'):
            print(f"      ✅ Decision: {block_meta['decision_choice']}")
            if block_meta.get('decision_reason'):
                print(f"         WHY: {block_meta['decision_reason']}")
        if block_meta.get('doc_filename'):
            print(f"      📄 Document: {block_meta['doc_filename']}")
            if block_meta.get('doc_location'):
                print(f"         Location: {block_meta['doc_location']}")

    # Propositions
    props = result.get(props_key, [])
    print(f"\n⚛️  Propositions ({len(props)}):")
    for i, prop in enumerate(props, 1):
        print(f"   {i}. {prop.get('content', 'N/A')}")
        # Show if prop has block metadata
        prop_blocks = prop.get('block_metadata', {})
        if prop_blocks and (prop_blocks.get('resource_url') or prop_blocks.get('decision_choice') or prop_blocks.get('doc_filename')):
            print(f"      [has blocks: {', '.join([k for k in ['resource_url', 'decision_choice', 'doc_filename'] if prop_blocks.get(k)])}]")

    # Timings
    t1 = result.get(time_key1, 0)
    t2 = result.get(time_key2, 0)
    print(f"\n⏱️  Timings:")
    print(f"   Stage 1: {t1:.2f}s | Stage 2: {t2:.2f}s | Total: {t1 + t2:.2f}s")
    print("-" * 80)


def get_conversation_context():
    """Get last 2 messages (1 conversation pair) as context."""
    if not conversation_history:
        return "Start of conversation"

    context = []
    for msg in conversation_history[-2:]:
        role = "User" if msg['role'] == 'user' else "Assistant"
        context.append(f"{role}: {msg['content']}")

    return "\n".join(context)


def run_extraction_async(batch_input):
    """Run extraction in background thread."""
    def _run():
        try:
            result = graph.invoke(batch_input)

            # Print extraction summaries
            print("\n" + "="*80)
            print("🧠 BACKGROUND EXTRACTION COMPLETE")
            print("="*80)
            print_extraction_summary("user", result)
            print_extraction_summary("assistant", result)

            # Storage summary
            stored_ids = result.get('stored_proposition_ids', [])
            embedding_time = result.get('embedding_time', 0)
            storage_time = result.get('storage_time', 0)
            edge_time = result.get('edge_creation_time', 0)

            print(f"\n💾 STORAGE:")
            print("-" * 80)
            print(f"   Propositions stored in Neo4j: {len(stored_ids)}")
            print(f"   Archive stored in SQLite: ✓")
            print(f"   Embeddings: {embedding_time:.2f}s | Storage: {storage_time:.2f}s | Edges: {edge_time:.2f}s")
            print("-" * 80)

            # Overall timing
            total_time = (
                result.get('stage1_user_time', 0) +
                result.get('stage1_assistant_time', 0) +
                result.get('stage2_user_time', 0) +
                result.get('stage2_assistant_time', 0) +
                embedding_time +
                storage_time +
                edge_time
            )
            print(f"\n⏱️  TOTAL BATCH PROCESSING TIME: {total_time:.2f}s")
            print(f"   (Stage 1: {result.get('stage1_user_time', 0) + result.get('stage1_assistant_time', 0):.2f}s | Stage 2: {result.get('stage2_user_time', 0) + result.get('stage2_assistant_time', 0):.2f}s | Storage: {embedding_time + storage_time + edge_time:.2f}s)")
            print("="*80 + "\n")
            print("👤 You: ", end="", flush=True)
        except Exception as e:
            print(f"\n❌ Background extraction error: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def chat_turn(user_input):
    """Process one turn of conversation with FIRE-AND-FORGET extraction."""
    global message_counter

    # Get chat response
    print("\n🤖 Assistant: ", end="", flush=True)

    # Build messages for chat
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_input})

    response = chat_model.invoke(messages)

    # Extract reasoning (thinking) if available
    thinking = None
    if hasattr(response, 'response_metadata'):
        thinking = response.response_metadata.get('thinking')

    # Display reasoning first (if available)
    if thinking:
        print("\n💭 REASONING:")
        print("-" * 80)
        print(thinking)
        print("-" * 80)
        print("\n🤖 Response: ", end="", flush=True)

    assistant_response = response.content
    print(assistant_response)

    # Prepare extraction (but don't wait for it)
    timestamp = datetime.now().isoformat()

    # Add to history first
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": assistant_response})

    message_counter += 1
    user_msg_id = f"msg_{message_counter:03d}"
    message_counter += 1
    assistant_msg_id = f"msg_{message_counter:03d}"

    # Capture reasoning if available (for storage in graph)
    reasoning_content = None
    if hasattr(response, 'response_metadata'):
        reasoning_content = response.response_metadata.get('thinking')

    # Send FULL conversation history - graph will extract context
    batch_input = {
        "user_message": user_input,
        "assistant_message": assistant_response,
        "assistant_reasoning": reasoning_content,  # NEW: reasoning capture
        "conversation_history": conversation_history[:-2],  # All messages BEFORE current pair
        "timestamp": timestamp,
        "user_message_id": user_msg_id,
        "assistant_message_id": assistant_msg_id
    }

    print("\n🚀 Extraction started in background...")
    run_extraction_async(batch_input)
    print_separator()


def main():
    """Main CLI loop."""
    print_separator()
    print("🧠 ReSemantic CLI Chat (FIRE-AND-FORGET Mode)")
    print("Conversational AI with Background Semantic Extraction")
    print("💬 Chat responds instantly | 🚀 Extraction runs in background")
    print("🏷️  NOW WITH BLOCKS DISPLAY!")
    print_separator()
    print("Commands:")
    print("  /exit or /quit - Exit chat")
    print("  /clear - Clear conversation history")
    print("  /history - Show conversation history")
    print("  /graph - Show Neo4j graph statistics")
    print_separator()

    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['/exit', '/quit']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == '/clear':
                conversation_history.clear()
                print("\n✅ Conversation history cleared!")
                continue

            if user_input.lower() == '/history':
                print("\n📜 Conversation History:")
                for i, msg in enumerate(conversation_history, 1):
                    role = "👤 You" if msg['role'] == 'user' else "🤖 Assistant"
                    print(f"\n{i}. {role}: {msg['content']}")
                continue

            if user_input.lower() == '/graph':
                print("\n📊 Neo4j Graph Statistics:")
                print("-" * 80)
                from storage import Neo4jClient
                neo4j = Neo4jClient(
                    uri="bolt://172.105.85.181:7687",
                    user="neo4j",
                    password="test1234"
                )
                try:
                    with neo4j.driver.session() as session:
                        # Count propositions
                        result = session.run("MATCH (p:Proposition) RETURN count(p) as count")
                        prop_count = result.single()['count']

                        # Count NEXT edges
                        result = session.run("MATCH ()-[r:NEXT]->() RETURN count(r) as count")
                        next_count = result.single()['count']

                        # Count COHERENT edges
                        result = session.run("MATCH ()-[r:COHERENT]->() RETURN count(r) as count")
                        coherent_count = result.single()['count']

                        print(f"   Propositions: {prop_count}")
                        print(f"   NEXT edges (temporal): {next_count}")
                        print(f"   COHERENT edges (semantic): {coherent_count}")
                        print(f"\n   Neo4j Browser: http://172.105.85.181:7474")
                finally:
                    neo4j.close()
                print("-" * 80)
                continue

            # Process chat turn with BATCH extraction
            chat_turn(user_input)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
