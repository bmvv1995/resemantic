#!/usr/bin/env python3
"""
Quick test for blocks extraction
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/opt/resemantic')

from graphs.extraction_graph import graph

# Test message with decision + resource
test_input = {
    "user_message": "am decis să folosesc webhook retry cu exponential backoff, docs la https://shopify.dev/api/retry și config în /opt/config/webhook.json",
    "assistant_message": "Excelent! Webhook retry cu exponential backoff e alegerea corectă pentru reliability. Vei avea nevoie și de monitoring.",
    "assistant_reasoning": None,
    "conversation_history": [],
    "timestamp": datetime.now().isoformat(),
    "user_message_id": "msg_001",
    "assistant_message_id": "msg_002"
}

print("🧪 TESTING BLOCKS EXTRACTION")
print("="*80)
print(f"\nUser message: {test_input['user_message']}")
print(f"Assistant message: {test_input['assistant_message']}")
print("\n" + "="*80)

result = graph.invoke(test_input)

print("\n📊 STAGE 1 - SEMANTIC UNITS:")
print("-"*80)

print("\n👤 USER SU:")
user_su = result.get('user_semantic_unit', {})
print(json.dumps(user_su, indent=2, ensure_ascii=False))

print("\n🤖 ASSISTANT SU:")
assistant_su = result.get('assistant_semantic_unit', {})
print(json.dumps(assistant_su, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("\n⚛️  STAGE 2 - PROPOSITIONS:")
print("-"*80)

print("\n👤 USER PROPS:")
for i, prop in enumerate(result.get('user_propositions', []), 1):
    print(f"\n{i}. Content: {prop.get('content')}")
    print(f"   Type: {prop.get('type')}")
    print(f"   Block metadata: {json.dumps(prop.get('block_metadata', {}), ensure_ascii=False)}")

print("\n🤖 ASSISTANT PROPS:")
for i, prop in enumerate(result.get('assistant_propositions', []), 1):
    print(f"\n{i}. Content: {prop.get('content')}")
    print(f"   Type: {prop.get('type')}")
    print(f"   Block metadata: {json.dumps(prop.get('block_metadata', {}), ensure_ascii=False)}")

print("\n" + "="*80)
print("\n✅ Test complete!")

