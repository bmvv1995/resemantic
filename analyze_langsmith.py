#!/usr/bin/env python3
"""
Analyze ReSemantic extractions from LangSmith
Validates FAZA 1 quality: atomic props, context resolution, blocks, concepts
"""

import os
import json
from datetime import datetime, timedelta
from langsmith import Client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# Initialize LangSmith client
client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))
project_name = os.getenv("LANGCHAIN_PROJECT", "resemantic-extraction")

print("="*80)
print("🔍 FAZA 1 VALIDATION - LangSmith Extraction Analysis")
print("="*80)
print(f"📊 Project: {project_name}")
print(f"🔗 URL: https://smith.langchain.com/projects/{project_name}")
print("="*80 + "\n")


# ============================================
# FETCH RECENT RUNS
# ============================================
print("📥 Fetching recent extraction runs...")

# Get runs from last 7 days
runs = list(client.list_runs(
    project_name=project_name,
    start_time=datetime.now() - timedelta(days=7),
    limit=50
))

print(f"✅ Found {len(runs)} runs in last 7 days\n")

if not runs:
    print("⚠️  No runs found. Run chat_cli_batch.py to generate data.")
    exit(0)


# ============================================
# ANALYZE EXTRACTION QUALITY
# ============================================

stats = {
    'total_runs': len(runs),
    'stage1_user': [],
    'stage1_assistant': [],
    'stage2_user': [],
    'stage2_assistant': [],
    'props_per_message': [],
    'props_atomicity': [],  # Manual validation
    'blocks_present': defaultdict(int),
    'decision_with_why': 0,
    'decision_without_why': 0,
    'concepts_quality': [],  # Generic vs specific
    'errors': []
}

print("🔬 ANALYZING EXTRACTION QUALITY\n")

for i, run in enumerate(runs[:20], 1):  # Analyze first 20
    print(f"\n{'='*80}")
    print(f"Run {i}/{min(20, len(runs))}: {run.name}")
    print(f"ID: {run.id}")
    print(f"Time: {run.start_time}")
    print(f"Status: {run.status}")

    # Get outputs
    if not run.outputs:
        print("⚠️  No outputs")
        continue

    outputs = run.outputs

    # ============================================
    # TEST 1: EXTRACTION COMPLETENESS
    # ============================================
    print(f"\n{'─'*80}")
    print("TEST 1: Extraction Completeness")
    print(f"{'─'*80}")

    user_su = outputs.get('user_semantic_unit', {})
    assistant_su = outputs.get('assistant_semantic_unit', {})
    user_props = outputs.get('user_propositions', [])
    assistant_props = outputs.get('assistant_propositions', [])

    print(f"✓ User SU: {'✅' if user_su else '❌'}")
    print(f"✓ Assistant SU: {'✅' if assistant_su else '❌'}")
    print(f"✓ User Props: {len(user_props)} props")
    print(f"✓ Assistant Props: {len(assistant_props)} props")

    stats['props_per_message'].append(len(user_props) + len(assistant_props))

    # ============================================
    # TEST 2: ATOMIC PROPOSITIONS
    # ============================================
    print(f"\n{'─'*80}")
    print("TEST 2: Atomic Propositions (Sample)")
    print(f"{'─'*80}")

    all_props = user_props + assistant_props
    for j, prop in enumerate(all_props[:3], 1):  # Show first 3
        content = prop.get('content', 'N/A')
        print(f"\nProp {j}: {content}")

        # Check atomicity heuristics
        warnings = []
        if ' and ' in content.lower():
            warnings.append("⚠️  Contains 'and' (might be compound)")
        if ' but ' in content.lower():
            warnings.append("⚠️  Contains 'but' (might be compound)")
        if content.count(',') > 2:
            warnings.append("⚠️  Multiple commas (might be list)")
        if len(content.split()) > 30:
            warnings.append("⚠️  >30 words (might not be atomic)")

        # Check concepts
        concepts = prop.get('concepts', [])
        print(f"   Concepts: {concepts}")

        if concepts:
            generic_concepts = [c for c in concepts if c.lower() in ['user', 'system', 'data', 'information', 'thing']]
            if generic_concepts:
                warnings.append(f"⚠️  Generic concepts: {generic_concepts}")

        if warnings:
            for w in warnings:
                print(f"   {w}")
        else:
            print("   ✅ Looks atomic")

    # ============================================
    # TEST 3: CONTEXT RESOLUTION
    # ============================================
    print(f"\n{'─'*80}")
    print("TEST 3: Context Resolution")
    print(f"{'─'*80}")

    user_content = user_su.get('content', '')
    print(f"User SU: {user_content[:200]}...")

    # Check for unresolved references
    unresolved = []
    if ' this ' in user_content.lower() or user_content.lower().strip().startswith('this'):
        unresolved.append("'this'")
    if ' that ' in user_content.lower():
        unresolved.append("'that'")
    if user_content.lower().strip() in ['da', 'yes', 'ok', 'sure']:
        unresolved.append("bare confirmation")

    if unresolved:
        print(f"⚠️  Possible unresolved: {', '.join(unresolved)}")
    else:
        print("✅ Context appears resolved")

    # ============================================
    # TEST 4: BLOCKS METADATA
    # ============================================
    print(f"\n{'─'*80}")
    print("TEST 4: Blocks Metadata")
    print(f"{'─'*80}")

    for su_name, su in [('User', user_su), ('Assistant', assistant_su)]:
        blocks = su.get('block_metadata', {})
        if blocks:
            print(f"\n{su_name} blocks:")

            # Resource block
            if blocks.get('resource_url'):
                print(f"   📎 Resource: {blocks['resource_url']}")
                print(f"      Type: {blocks.get('resource_type', 'N/A')}")
                stats['blocks_present']['resource'] += 1

            # Decision block
            if blocks.get('decision_choice'):
                print(f"   ✅ Decision: {blocks['decision_choice']}")
                reason = blocks.get('decision_reason', '')
                if reason:
                    print(f"      WHY: {reason}")
                    stats['decision_with_why'] += 1
                else:
                    print(f"      ⚠️  WHY: MISSING!")
                    stats['decision_without_why'] += 1
                stats['blocks_present']['decision'] += 1

            # Document block
            if blocks.get('doc_filename'):
                print(f"   📄 Document: {blocks['doc_filename']}")
                print(f"      Location: {blocks.get('doc_location', 'N/A')}")
                stats['blocks_present']['document'] += 1
        else:
            print(f"{su_name}: No blocks")

    # ============================================
    # TEST 5: TIMINGS
    # ============================================
    print(f"\n{'─'*80}")
    print("TEST 5: Performance Timings")
    print(f"{'─'*80}")

    t1_user = outputs.get('stage1_user_time', 0)
    t1_assistant = outputs.get('stage1_assistant_time', 0)
    t2_user = outputs.get('stage2_user_time', 0)
    t2_assistant = outputs.get('stage2_assistant_time', 0)
    t_embedding = outputs.get('embedding_time', 0)
    t_storage = outputs.get('storage_time', 0)
    t_edges = outputs.get('edge_creation_time', 0)

    total = t1_user + t1_assistant + t2_user + t2_assistant + t_embedding + t_storage + t_edges

    print(f"Stage 1 (SU extraction): {t1_user + t1_assistant:.2f}s")
    print(f"Stage 2 (Propositionalize): {t2_user + t2_assistant:.2f}s")
    print(f"Storage: {t_embedding + t_storage + t_edges:.2f}s")
    print(f"TOTAL: {total:.2f}s")

    stats['stage1_user'].append(t1_user)
    stats['stage1_assistant'].append(t1_assistant)
    stats['stage2_user'].append(t2_user)
    stats['stage2_assistant'].append(t2_assistant)

    # Errors
    if outputs.get('error'):
        print(f"\n❌ ERROR: {outputs['error']}")
        stats['errors'].append(outputs['error'])


# ============================================
# SUMMARY STATISTICS
# ============================================
print("\n\n" + "="*80)
print("📊 SUMMARY STATISTICS")
print("="*80)

print(f"\n📈 Runs Analyzed: {min(20, len(runs))}")

if stats['props_per_message']:
    avg_props = sum(stats['props_per_message']) / len(stats['props_per_message'])
    print(f"\n⚛️  Propositions:")
    print(f"   Average per message pair: {avg_props:.1f}")
    print(f"   Min: {min(stats['props_per_message'])}")
    print(f"   Max: {max(stats['props_per_message'])}")

if stats['stage1_user']:
    print(f"\n⏱️  Stage 1 Timings (Semantic Units):")
    print(f"   User avg: {sum(stats['stage1_user'])/len(stats['stage1_user']):.2f}s")
    print(f"   Assistant avg: {sum(stats['stage1_assistant'])/len(stats['stage1_assistant']):.2f}s")

if stats['stage2_user']:
    print(f"\n⏱️  Stage 2 Timings (Propositionalize):")
    print(f"   User avg: {sum(stats['stage2_user'])/len(stats['stage2_user']):.2f}s")
    print(f"   Assistant avg: {sum(stats['stage2_assistant'])/len(stats['stage2_assistant']):.2f}s")

print(f"\n🏷️  Blocks Metadata:")
for block_type, count in stats['blocks_present'].items():
    print(f"   {block_type.capitalize()}: {count} occurrences")

if stats['decision_with_why'] + stats['decision_without_why'] > 0:
    total_decisions = stats['decision_with_why'] + stats['decision_without_why']
    why_rate = (stats['decision_with_why'] / total_decisions) * 100
    print(f"\n✅ Decision WHY Capture Rate: {why_rate:.1f}%")
    print(f"   With WHY: {stats['decision_with_why']}")
    print(f"   Without WHY: {stats['decision_without_why']}")

if stats['errors']:
    print(f"\n❌ Errors: {len(stats['errors'])}")
    for err in stats['errors'][:3]:
        print(f"   - {err}")


# ============================================
# QUALITY ASSESSMENT
# ============================================
print("\n\n" + "="*80)
print("🎯 QUALITY ASSESSMENT")
print("="*80)

print("\n✅ GREEN LIGHTS (Good to proceed):")
green_lights = []

if avg_props >= 2 and avg_props <= 8:
    green_lights.append("✓ Proposition count in expected range (2-8)")
if stats['decision_with_why'] > 0:
    green_lights.append("✓ Decision blocks capture WHY")
if len(stats['errors']) == 0:
    green_lights.append("✓ No extraction errors")

if green_lights:
    for gl in green_lights:
        print(f"   {gl}")
else:
    print("   (None detected in sample)")

print("\n⚠️  YELLOW FLAGS (Review needed):")
yellow_flags = []

if stats['decision_without_why'] > 0:
    yellow_flags.append(f"⚠️  {stats['decision_without_why']} decisions missing WHY")
if avg_props < 2:
    yellow_flags.append(f"⚠️  Low prop count ({avg_props:.1f} avg) - might be under-extracting")
if avg_props > 10:
    yellow_flags.append(f"⚠️  High prop count ({avg_props:.1f} avg) - might not be atomic")

if yellow_flags:
    for yf in yellow_flags:
        print(f"   {yf}")
else:
    print("   (None detected in sample)")

print("\n🚨 RED FLAGS (Fix before FAZA 2):")
red_flags = []

if len(stats['errors']) > len(runs) * 0.2:
    red_flags.append(f"🚨 High error rate: {len(stats['errors'])}/{len(runs)}")
if stats['decision_with_why'] == 0 and stats['decision_without_why'] > 3:
    red_flags.append("🚨 NO decisions have WHY captured")

if red_flags:
    for rf in red_flags:
        print(f"   {rf}")
else:
    print("   ✅ None detected!")


# ============================================
# RECOMMENDATIONS
# ============================================
print("\n\n" + "="*80)
print("💡 RECOMMENDATIONS")
print("="*80)

print("\n1️⃣  MANUAL DEEP DIVE:")
print("   - Review sample propositions above for atomicity")
print("   - Check if context resolution works (no ambiguous 'this'/'that')")
print("   - Verify concepts are specific (not generic)")

print("\n2️⃣  NEXT VALIDATION:")
print("   - Test semantic similarity (do related props have high cosine?)")
print("   - Check COHERENT edges quality (are neighbors truly related?)")
print("   - Validate retrieval precision (query → relevant props?)")

print("\n3️⃣  IF QUALITY IS GOOD:")
print("   - ✅ Proceed to graph traversal implementation")
print("   - ✅ Start sleep cycles design")

print("\n4️⃣  IF ISSUES FOUND:")
print("   - 🔧 Tune extraction prompts")
print("   - 🔧 Adjust block extraction instructions")
print("   - 🔧 Re-run validation")

print("\n" + "="*80)
print("🔗 View full traces: https://smith.langchain.com/")
print("="*80 + "\n")
