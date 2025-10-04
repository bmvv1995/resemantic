"""
Process Conversation - End-to-End Pipeline

Raw conversation JSON → Extraction (LangGraph) → Dual Storage (Neo4j + SQLite)
"""

import json
import asyncio
from graphs import extraction_graph
from storage import Neo4jClient
from datetime import datetime


async def process_conversation(conversation_file: str):
    """
    Process entire conversation through extraction pipeline.

    Args:
        conversation_file: Path to JSON file with conversation
    """

    print("="*70)
    print("RESEMANTIC - END-TO-END CONVERSATION PROCESSING")
    print("="*70 + "\n")

    # Load conversation
    print(f"📖 Loading conversation from {conversation_file}...")
    with open(conversation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data['conversation']
    print(f"✅ Loaded {len(messages)} messages\n")

    # Process message pairs (user + assistant)
    total_propositions = 0
    pair_count = 0

    for i in range(0, len(messages) - 1, 2):
        if i + 1 >= len(messages):
            break

        user_msg = messages[i]
        asst_msg = messages[i + 1]

        pair_count += 1

        print(f"{'='*70}")
        print(f"PAIR {pair_count}/{len(messages)//2}")
        print(f"{'='*70}")
        print(f"👤 User: {user_msg['content'][:60]}...")
        print(f"🤖 Assistant: {asst_msg['content'][:60]}...\n")

        # Build context (previous messages)
        context = "Start of conversation"
        if i > 0:
            context_msgs = messages[max(0, i-4):i]
            context = "\n".join([
                f"{msg['role']}: {msg['content'][:100]}..."
                for msg in context_msgs
            ])

        # Invoke extraction graph
        print("🔄 Processing through extraction pipeline...")

        try:
            result = await extraction_graph.ainvoke({
                "user_message": user_msg['content'],
                "assistant_message": asst_msg['content'],
                "conversation_context": context,
                "timestamp": user_msg.get('timestamp', datetime.now().isoformat()),
                "user_message_id": f"msg_{i+1:03d}",
                "assistant_message_id": f"msg_{i+2:03d}"
            })

            # Results
            print(f"\n📊 RESULTS:")
            print(f"   User Semantic Unit: {result['user_semantic_unit'].get('type', 'N/A')}")
            print(f"   Assistant Semantic Unit: {result['assistant_semantic_unit'].get('type', 'N/A')}")
            print(f"   User Propositions: {len(result['user_propositions'])}")
            print(f"   Assistant Propositions: {len(result['assistant_propositions'])}")
            print(f"   Stored in Neo4j: {len(result['stored_proposition_ids'])} propositions")

            total_propositions += len(result['stored_proposition_ids'])

            # Timing
            total_time = (
                result.get('stage1_user_time', 0) +
                result.get('stage1_assistant_time', 0) +
                result.get('stage2_user_time', 0) +
                result.get('stage2_assistant_time', 0) +
                result.get('storage_time', 0)
            )

            print(f"\n⏱️  TIMING:")
            print(f"   Stage 1: {result.get('stage1_user_time', 0) + result.get('stage1_assistant_time', 0):.2f}s")
            print(f"   Stage 2: {result.get('stage2_user_time', 0) + result.get('stage2_assistant_time', 0):.2f}s")
            print(f"   Storage: {result.get('storage_time', 0):.2f}s")
            print(f"   TOTAL: {total_time:.2f}s\n")

        except Exception as e:
            print(f"❌ Error processing pair {pair_count}: {e}\n")
            import traceback
            traceback.print_exc()
            continue

    # Final stats
    print("="*70)
    print("PROCESSING COMPLETE")
    print("="*70 + "\n")

    # Query Neo4j for final stats
    neo4j = Neo4jClient(
        uri="bolt://172.105.85.181:7687",
        user="neo4j",
        password="test1234"
    )

    prop_count = neo4j.count_propositions()
    edge_counts = neo4j.count_edges()

    print(f"📊 FINAL STATISTICS:")
    print(f"   Message pairs processed: {pair_count}")
    print(f"   Total propositions created: {total_propositions}")
    print(f"\n   Neo4j Graph:")
    print(f"      Propositions: {prop_count}")
    for edge_type, count in edge_counts.items():
        print(f"      {edge_type} edges: {count}")

    print(f"\n   SQLite Archive:")
    print(f"      Database: data/resemantic_archive.db")
    print(f"      Full traceability: Message → SemanticUnit → Proposition")

    neo4j.close()

    print(f"\n{'='*70}")
    print("✅ SUCCESS! Conversation processed and stored.")
    print("="*70)
    print("\n🎯 Next steps:")
    print("   - Visualize in Neo4j Browser: http://172.105.85.181:7474")
    print("   - Query propositions with vector search")
    print("   - Test retrieval with sample queries")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        conversation_file = sys.argv[1]
    else:
        conversation_file = "test_conversation.json"

    print(f"\nProcessing: {conversation_file}\n")

    asyncio.run(process_conversation(conversation_file))
