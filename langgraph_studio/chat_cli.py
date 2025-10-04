#!/usr/bin/env python3
"""
ReSemantic CLI Chat - Conversational interface with semantic extraction
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from extraction_graph import graph

# Load environment
load_dotenv()

# Initialize chat model
chat_model = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.7,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Conversation history
conversation_history = []
message_counter = 0


def print_separator():
    print("\n" + "="*80 + "\n")


def print_extraction_summary(result):
    """Print extraction results in a readable format."""
    print("\n📊 SEMANTIC EXTRACTION:")
    print("-" * 80)

    # Semantic Unit
    su = result.get('semantic_unit', {})
    print(f"📝 Semantic Unit: {su.get('content', 'N/A')}")
    print(f"   Type: {su.get('type', 'N/A')} | Role: {su.get('narrative_role', 'N/A')}")
    print(f"   Concepts: {', '.join(su.get('concepts', []))}")

    # Propositions
    props = result.get('propositions', [])
    print(f"\n⚛️  Propositions ({len(props)}):")
    for i, prop in enumerate(props, 1):
        print(f"   {i}. {prop.get('content', 'N/A')}")

    # Timings
    print(f"\n⏱️  Timings:")
    print(f"   Stage 1: {result.get('stage1_time', 0):.2f}s | Stage 2: {result.get('stage2_time', 0):.2f}s")
    print(f"   Total: {result.get('stage1_time', 0) + result.get('stage2_time', 0):.2f}s")
    print("-" * 80)


def get_conversation_context():
    """Get last 3 messages as context."""
    if not conversation_history:
        return "Start of conversation"

    context = []
    for msg in conversation_history[-3:]:
        role = "User" if msg['role'] == 'user' else "Assistant"
        context.append(f"{role}: {msg['content']}")

    return "\n".join(context)


def chat_turn(user_input):
    """Process one turn of conversation with extraction."""
    global message_counter

    # Get chat response
    print("\n🤖 Assistant: ", end="", flush=True)

    # Build messages for chat
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_input})

    response = chat_model.invoke(messages)
    assistant_response = response.content

    print(assistant_response)

    # Add to history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": assistant_response})

    print("\n🧠 Extracting semantic knowledge...")

    timestamp = datetime.now().isoformat()
    context = get_conversation_context()

    # Extract from USER message
    print("\n[1/2] Processing USER message...")
    message_counter += 1
    user_extraction_input = {
        "message_content": user_input,
        "conversation_context": context,
        "role": "user",
        "timestamp": timestamp,
        "message_id": f"msg_{message_counter:03d}"
    }
    user_result = graph.invoke(user_extraction_input)
    print_extraction_summary(user_result)

    # Extract from ASSISTANT message
    print("\n[2/2] Processing ASSISTANT message...")
    message_counter += 1
    assistant_extraction_input = {
        "message_content": assistant_response,
        "conversation_context": context,
        "role": "assistant",
        "timestamp": timestamp,
        "message_id": f"msg_{message_counter:03d}"
    }
    assistant_result = graph.invoke(assistant_extraction_input)
    print_extraction_summary(assistant_result)

    return {"user": user_result, "assistant": assistant_result}


def main():
    """Main CLI loop."""
    print_separator()
    print("🧠 ReSemantic CLI Chat")
    print("Conversational AI with Semantic Extraction")
    print_separator()
    print("Commands:")
    print("  /exit or /quit - Exit chat")
    print("  /clear - Clear conversation history")
    print("  /history - Show conversation history")
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

            # Process chat turn
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
