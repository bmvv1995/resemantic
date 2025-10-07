#!/usr/bin/env python3
"""
Deep validation of FAZA 1 - Direct Neo4j analysis
Sample actual stored propositions and validate quality
"""

import sys
import os
import json
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import Neo4jClient
from config import Neo4jConfig

print("="*80)
print("🔬 DEEP FAZA 1 VALIDATION - Neo4j Direct Analysis")
print("="*80 + "\n")

neo4j = Neo4jClient(
    uri=Neo4jConfig.URI,
    user=Neo4jConfig.USER,
    password=Neo4jConfig.PASSWORD
)

# ============================================
# GRAPH STATISTICS
# ============================================
print("📊 GRAPH STATISTICS")
print("-"*80)

with neo4j.driver.session() as session:
    # Total propositions
    result = session.run("MATCH (p:Proposition) RETURN count(p) as count")
    total_props = result.single()['count']
    print(f"Total Propositions: {total_props}")

    # NEXT edges
    result = session.run("MATCH ()-[r:NEXT]->() RETURN count(r) as count")
    next_count = result.single()['count']
    print(f"NEXT edges (temporal): {next_count}")

    # COHERENT edges
    result = session.run("MATCH ()-[r:COHERENT]-() RETURN count(r)/2 as count")
    coherent_count = int(result.single()['count'])
    print(f"COHERENT edges (semantic): {coherent_count}")

    # Speaker distribution
    result = session.run("""
        MATCH (p:Proposition)
        RETURN p.speaker as speaker, count(p) as count
    """)
    print(f"\nSpeaker Distribution:")
    for record in result:
        print(f"   {record['speaker']}: {record['count']} props")

    # Type distribution
    result = session.run("""
        MATCH (p:Proposition)
        RETURN p.type as type, count(p) as count
        ORDER BY count DESC
    """)
    print(f"\nType Distribution:")
    for record in result:
        print(f"   {record['type']}: {record['count']}")

print("\n" + "="*80)
print("🔍 SAMPLE PROPOSITIONS - QUALITY CHECK")
print("="*80 + "\n")

# ============================================
# SAMPLE 10 RANDOM PROPOSITIONS
# ============================================
with neo4j.driver.session() as session:
    result = session.run("""
        MATCH (p:Proposition)
        RETURN p
        ORDER BY rand()
        LIMIT 10
    """)

    props = [dict(record['p']) for record in result]

for i, p in enumerate(props, 1):
    print(f"\n{'─'*80}")
    print(f"PROPOSITION {i}/10")
    print(f"{'─'*80}")

    content = p.get('content', 'N/A')
    print(f"📝 Content: {content}")

    # Atomicity check
    atomicity_warnings = []
    if ' and ' in content.lower() and content.count(' and ') > 1:
        atomicity_warnings.append("Multiple 'and' conjunctions")
    if ' but ' in content.lower():
        atomicity_warnings.append("Contains 'but' (potential contrast)")
    if content.count(',') > 2:
        atomicity_warnings.append(f"{content.count(',')} commas (list?)")
    if len(content.split()) > 35:
        atomicity_warnings.append(f"{len(content.split())} words (too long?)")

    # Context resolution check
    context_issues = []
    content_lower = content.lower()
    if content_lower.strip() in ['da', 'yes', 'ok', 'sure', 'no']:
        context_issues.append("Bare confirmation/denial")
    if ' this ' in content_lower or content_lower.startswith('this '):
        # Check if 'this' is followed by a noun (resolved) or not
        if ' this.' in content_lower or content_lower.endswith(' this'):
            context_issues.append("Unresolved 'this'")
    if ' that ' in content_lower and ' that.' in content_lower:
        context_issues.append("Possibly unresolved 'that'")

    print(f"\n🔬 Metadata:")
    print(f"   Type: {p.get('type', 'N/A')}")
    print(f"   Certainty: {p.get('certainty', 'N/A')}")
    print(f"   Speaker: {p.get('speaker', 'N/A')}")

    # Concepts
    concepts = p.get('concepts', [])
    print(f"   Concepts: {concepts if concepts else 'NONE'}")

    # Check concept quality
    if concepts:
        generic_concepts = []
        specific_concepts = []
        for c in concepts:
            c_lower = c.lower()
            if c_lower in ['user', 'system', 'data', 'information', 'thing', 'assistant', 'message']:
                generic_concepts.append(c)
            elif '_' in c or len(c.split()) > 1:  # Compound concepts
                specific_concepts.append(c)
            else:
                specific_concepts.append(c)

        if generic_concepts:
            print(f"   ⚠️  Generic concepts: {generic_concepts}")
        if specific_concepts:
            print(f"   ✅ Specific concepts: {specific_concepts}")

    # Blocks
    block_meta = p.get('block_metadata', '{}')
    if isinstance(block_meta, str):
        try:
            blocks = json.loads(block_meta)
        except:
            blocks = {}
    else:
        blocks = block_meta

    if blocks and any(v for v in blocks.values() if v):
        print(f"\n🏷️  Blocks:")
        if blocks.get('resource_url'):
            print(f"   📎 Resource: {blocks['resource_url']}")
            print(f"      Type: {blocks.get('resource_type', 'N/A')}")
        if blocks.get('decision_choice'):
            print(f"   ✅ Decision: {blocks['decision_choice']}")
            reason = blocks.get('decision_reason', '')
            if reason:
                print(f"      WHY: {reason}")
            else:
                print(f"      ⚠️  WHY: MISSING")
        if blocks.get('doc_filename'):
            print(f"   📄 Document: {blocks['doc_filename']}")
            print(f"      Location: {blocks.get('doc_location', 'N/A')}")

    # Quality assessment
    print(f"\n⚖️  Quality Assessment:")
    issues = []

    if atomicity_warnings:
        issues.append(f"❌ Atomicity: {', '.join(atomicity_warnings)}")
    else:
        print(f"   ✅ Atomicity: Looks atomic")

    if context_issues:
        issues.append(f"❌ Context: {', '.join(context_issues)}")
    else:
        print(f"   ✅ Context: Appears resolved")

    if not concepts or len(concepts) == 0:
        issues.append(f"⚠️  No concepts extracted")

    if issues:
        for issue in issues:
            print(f"   {issue}")


# ============================================
# COHERENT EDGES QUALITY CHECK
# ============================================
print("\n\n" + "="*80)
print("🔗 SEMANTIC EDGES QUALITY")
print("="*80 + "\n")

with neo4j.driver.session() as session:
    # Get a prop with many neighbors
    result = session.run("""
        MATCH (p:Proposition)-[r:COHERENT]-(n)
        WITH p, count(r) as degree
        WHERE degree > 3
        ORDER BY degree DESC
        LIMIT 1
        RETURN p, degree
    """)

    record = result.single()
    if record:
        central_prop = dict(record['p'])
        degree = record['degree']

        print(f"Central Proposition (degree={degree}):")
        print(f"📝 {central_prop['content']}\n")

        # Get neighbors
        result = session.run("""
            MATCH (p:Proposition {id: $id})-[r:COHERENT]-(n:Proposition)
            RETURN n.content as content, r.weight as weight
            ORDER BY r.weight DESC
            LIMIT 8
        """, {"id": central_prop['id']})

        print(f"Top 8 Semantic Neighbors:")
        print("-"*80)
        neighbors = list(result)
        for i, neighbor in enumerate(neighbors, 1):
            print(f"{i}. [{neighbor['weight']:.3f}] {neighbor['content'][:100]}...")

        print(f"\n🔬 Manual Check:")
        print(f"   ✓ Are neighbors 1-3 (highest similarity) truly semantically related?")
        print(f"   ✓ Are neighbors 6-8 (lower similarity) still somewhat relevant?")
        print(f"   ✓ If not, threshold 0.4 might be too low (creates noise)")
    else:
        print("⚠️  No propositions with COHERENT edges found")


# ============================================
# DECISION BLOCKS ANALYSIS
# ============================================
print("\n\n" + "="*80)
print("✅ DECISION BLOCKS - WHY CAPTURE RATE")
print("="*80 + "\n")

with neo4j.driver.session() as session:
    # Get all props with decision blocks
    result = session.run("""
        MATCH (p:Proposition)
        WHERE p.block_metadata CONTAINS 'decision_choice'
        RETURN p.content as content, p.block_metadata as blocks
        LIMIT 20
    """)

    records = list(result)

    if records:
        with_why = 0
        without_why = 0

        print(f"Found {len(records)} decision propositions:\n")

        for i, record in enumerate(records[:10], 1):  # Show first 10
            blocks = json.loads(record['blocks'])
            decision = blocks.get('decision_choice', 'N/A')
            reason = blocks.get('decision_reason', '')

            print(f"{i}. Decision: {decision}")
            if reason:
                print(f"   WHY: {reason[:100]}...")
                print(f"   ✅ WHY captured")
                with_why += 1
            else:
                print(f"   ❌ WHY MISSING")
                without_why += 1
            print()

        total = with_why + without_why
        if total > 0:
            rate = (with_why / total) * 100
            print(f"\n📊 WHY Capture Rate: {rate:.1f}%")
            print(f"   With WHY: {with_why}/{total}")
            print(f"   Without WHY: {without_why}/{total}")

            if rate >= 90:
                print(f"   ✅ Excellent! WHY is consistently captured")
            elif rate >= 70:
                print(f"   ⚠️  Good, but some decisions missing WHY")
            else:
                print(f"   🚨 Poor - many decisions lack WHY (prompt issue?)")
    else:
        print("⚠️  No decision blocks found in graph")


# ============================================
# FINAL VERDICT
# ============================================
print("\n\n" + "="*80)
print("🎯 FINAL VERDICT - FAZA 1 QUALITY")
print("="*80 + "\n")

print("Based on the analysis above, answer these questions:\n")

print("1️⃣  EXTRACTION QUALITY:")
print("   ✓ Are propositions atomic (single verifiable statements)?")
print("   ✓ Is context resolved (no ambiguous 'this'/'that'/'da')?")
print("   ✓ Are concepts specific (not generic)?")

print("\n2️⃣  BLOCKS QUALITY:")
print("   ✓ Do decision blocks consistently capture WHY?")
print("   ✓ Are resource URLs complete?")
print("   ✓ Are blocks populated when relevant?")

print("\n3️⃣  GRAPH QUALITY:")
print("   ✓ Do COHERENT edges connect truly related propositions?")
print("   ✓ Is the similarity threshold (0.4) appropriate?")
print("   ✓ Are there enough edges (avg 5-10 per node)?")

print("\n" + "-"*80)
print("✅ GREEN LIGHT → Proceed to graph traversal + sleep cycles")
print("⚠️  YELLOW → Tune prompts, adjust thresholds, re-validate")
print("🚨 RED LIGHT → Fix fundamental issues before FAZA 2")
print("-"*80 + "\n")

neo4j.close()

print("🔗 Review full extraction traces:")
print("   https://smith.langchain.com/")
print("\n" + "="*80)
