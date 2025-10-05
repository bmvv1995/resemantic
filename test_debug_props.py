#!/usr/bin/env python3
"""Debug - see what generate_embeddings outputs"""

import sys
sys.path.insert(0, '/opt/resemantic')

from graphs.extraction_graph import graph
from datetime import datetime
import json

test_input = {
    "user_message": "am decis webhook retry, docs la https://shopify.dev/api/retry",
    "assistant_message": "Excelent! Bună decizie.",
    "assistant_reasoning": None,
    "conversation_history": [],
    "timestamp": datetime.now().isoformat(),
    "user_message_id": "msg_001",
    "assistant_message_id": "msg_002"
}

print("🔍 DEBUGGING - What does generate_embeddings output?")
print("="*80)

result = graph.invoke(test_input)

print("\n📦 ALL_PROPOSITIONS (from generate_embeddings):")
print("-"*80)

all_props = result.get('all_propositions', [])
print(f"\nTotal propositions: {len(all_props)}")

for i, prop in enumerate(all_props[:2], 1):  # First 2
    print(f"\n{i}. Content: {prop.get('content', 'N/A')[:60]}...")
    print(f"   Keys in prop: {list(prop.keys())}")
    print(f"   block_metadata present: {'block_metadata' in prop}")
    if 'block_metadata' in prop:
        print(f"   block_metadata value: {json.dumps(prop['block_metadata'], indent=4)}")

