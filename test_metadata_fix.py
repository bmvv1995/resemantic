#!/usr/bin/env python3
"""Test metadata encoding fix - verify dict flow"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import Neo4jClient
from config import Neo4jConfig

neo4j = Neo4jClient(
    uri=Neo4jConfig.URI,
    user=Neo4jConfig.USER,
    password=Neo4jConfig.PASSWORD
)

print("="*80)
print("🔬 METADATA FIX VALIDATION")
print("="*80 + "\n")

with neo4j.driver.session() as session:
    # Get all props
    result = session.run("MATCH (p:Proposition) RETURN p LIMIT 5")
    props = [dict(record['p']) for record in result]

print(f"📊 Found {len(props)} propositions\n")

for i, p in enumerate(props, 1):
    print(f"{'─'*80}")
    print(f"PROP {i}:")
    print(f"Content: {p['content'][:80]}...")
    print(f"\n📦 block_metadata field:")
    print(f"   Type: {type(p.get('block_metadata'))}")

    bm = p.get('block_metadata', '{}')
    print(f"   Raw value: {bm[:200] if isinstance(bm, str) else bm}")

    # Try to parse
    try:
        if isinstance(bm, str):
            parsed = json.loads(bm)
            print(f"   ✅ Parsed as: {type(parsed)}")
            if parsed:
                print(f"   Fields: {list(parsed.keys())}")
                if 'decision_choice' in parsed:
                    print(f"   🎯 Decision: {parsed['decision_choice']}")
                    print(f"   🎯 WHY: {parsed.get('decision_reason', 'MISSING')}")
        else:
            print(f"   ⚠️  Not a string - type: {type(bm)}")
    except Exception as e:
        print(f"   ❌ Parse error: {e}")

    print()

print("="*80)
print("✅ VALIDATION COMPLETE")
print("="*80)

neo4j.close()
