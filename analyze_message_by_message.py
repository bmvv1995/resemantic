"""
Message-by-message proposition analysis.
Processes each message individually and compares Baseline vs DSPy output.
"""

import json
import dspy
from dspy_propositions import PropositionExtractor, BaselinePropositionExtractor
from typing import List, Dict
from dotenv import load_dotenv
import os


def analyze_message_by_message(conversation_file: str, api_key: str, output_file: str):
    """Process each message individually and compare results."""

    # Setup
    print("🔧 Setting up models...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    baseline_extractor = BaselinePropositionExtractor(lm)
    dspy_extractor = PropositionExtractor()

    # Load conversation
    with open(conversation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    messages = data['conversation']

    print(f"📖 Processing {len(messages)} messages individually...\n")

    results = {
        "metadata": {
            "total_messages": len(messages),
            "processing_mode": "message-by-message (incremental context)"
        },
        "messages": []
    }

    # Process each message with growing context
    for idx, msg in enumerate(messages):
        print(f"{'='*70}")
        print(f"MESSAGE {idx + 1}/{len(messages)} - {msg['role'].upper()}")
        print(f"{'='*70}")
        print(f"Content: {msg['content'][:100]}...")
        print()

        # Build context from previous messages
        context = build_context(messages, idx, window=3)

        # Extract with Baseline
        print("🔵 Extracting with Baseline...")
        baseline_props = baseline_extractor.extract(
            message_content=msg['content'],
            conversation_context=context,
            role=msg['role']
        )

        print(f"   → {len(baseline_props)} propositions")

        # Extract with DSPy
        print("🟢 Extracting with DSPy...")
        dspy_props = dspy_extractor.forward(
            message_content=msg['content'],
            conversation_context=context,
            role=msg['role']
        )

        print(f"   → {len(dspy_props)} propositions")
        print()

        # Store results
        message_result = {
            "message_index": idx + 1,
            "role": msg['role'],
            "timestamp": msg['timestamp'],
            "original_content": msg['content'],
            "context_used": context,
            "baseline": {
                "count": len(baseline_props),
                "propositions": [
                    {
                        "content": p.content,
                        "type": p.type,
                        "certainty": p.certainty,
                        "concepts": p.concepts
                    }
                    for p in baseline_props
                ]
            },
            "dspy": {
                "count": len(dspy_props),
                "propositions": [
                    {
                        "content": p.content,
                        "type": p.type,
                        "certainty": p.certainty,
                        "concepts": p.concepts
                    }
                    for p in dspy_props
                ]
            }
        }

        results["messages"].append(message_result)

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis complete! Saved to {output_file}")

    # Print summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")

    baseline_total = sum(m['baseline']['count'] for m in results['messages'])
    dspy_total = sum(m['dspy']['count'] for m in results['messages'])

    print(f"\nTotal propositions:")
    print(f"  Baseline: {baseline_total}")
    print(f"  DSPy:     {dspy_total}")
    print(f"  Diff:     {baseline_total - dspy_total} ({'+' if baseline_total > dspy_total else ''}{baseline_total - dspy_total})")

    print(f"\nPer message average:")
    print(f"  Baseline: {baseline_total / len(messages):.1f}")
    print(f"  DSPy:     {dspy_total / len(messages):.1f}")


def build_context(messages: List[Dict], current_idx: int, window: int = 3) -> str:
    """Build conversation context from previous messages."""
    if current_idx == 0:
        return "Start of conversation"

    start = max(0, current_idx - window)
    context_msgs = messages[start:current_idx]

    return "\n".join([
        f"{msg['role']}: {msg['content'][:200]}..."
        for msg in context_msgs
    ])


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY in .env file")
        exit(1)

    analyze_message_by_message(
        conversation_file="/opt/resemantic/test_conversation.json",
        api_key=api_key,
        output_file="/opt/resemantic/message_by_message_analysis.json"
    )
