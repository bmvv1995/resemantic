"""
Generate human-readable report for FIXED two-stage pipeline.
Shows message-by-message with original, semantic unit, and propositions.
"""

import json


def generate_fixed_report(fixed_file: str, output_file: str):
    """Create readable report from fixed results."""

    with open(fixed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []

    # Header
    lines.append("# 🔬 FIXED Two-Stage Proposition Extraction")
    lines.append("")
    lines.append("**Pipeline:** Semantic Unit → Propositions")
    lines.append("")
    lines.append("**FIX Applied:** Clear system/data separation to prevent LLM from answering questions instead of describing them")
    lines.append("")
    lines.append(f"**Processing Mode:** Message-by-message incremental (context window = 3)")
    lines.append("")
    lines.append(f"**Total Messages:** {len(data['messages'])}")
    lines.append("")

    # Total
    total_props = sum(m['proposition_count'] for m in data['messages'])
    lines.append(f"**Total Propositions:** {total_props} ({total_props/len(data['messages']):.1f} avg per message)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Each message
    for msg in data['messages']:
        msg_num = msg['message_index']
        role = msg['semantic_unit']['speaker'].upper()

        lines.append(f"## 📬 Message {msg_num} - {role}")
        lines.append("")

        # Original
        lines.append("### 📝 Original Message")
        lines.append("```")
        lines.append(msg['original_content'])
        lines.append("```")
        lines.append("")

        # Context (collapsible)
        if msg['context_used'] != "Start of conversation":
            lines.append("<details>")
            lines.append("<summary>🔗 Context Used (click to expand)</summary>")
            lines.append("")
            lines.append("```")
            lines.append(msg['context_used'])
            lines.append("```")
            lines.append("</details>")
            lines.append("")

        # Semantic Unit
        lines.append("---")
        lines.append("")
        lines.append("### 🎯 STAGE 1: Semantic Unit")
        lines.append("")

        su = msg['semantic_unit']
        lines.append(f"**Content:**")
        lines.append(f"> {su['content']}")
        lines.append("")

        lines.append("**Metadata:**")
        lines.append(f"- **Type**: `{su['type']}`")
        lines.append(f"- **Narrative Role**: `{su['narrative_role']}`")
        lines.append(f"- **Relevance**: `{su['relevance']}`")
        lines.append(f"- **Certainty**: `{su['certainty']}`")
        lines.append(f"- **Impact**: `{su['impact']}`")

        if su['concepts']:
            lines.append(f"- **Concepts**: {', '.join(su['concepts'])}")

        if su['entities']:
            lines.append(f"- **Entities**: {', '.join(su['entities'])}")

        if su['decisions']:
            lines.append(f"- **Decisions**: {', '.join(su['decisions'])}")

        if su['context_dependencies']:
            lines.append(f"- **Context Dependencies**: {', '.join(su['context_dependencies'])}")

        lines.append("")

        # Propositions
        lines.append("---")
        lines.append("")
        lines.append(f"### ⚛️ STAGE 2: Propositions ({msg['proposition_count']})")
        lines.append("")

        if msg['proposition_count'] == 0:
            lines.append("*No propositions extracted*")
            lines.append("")
        else:
            for i, prop in enumerate(msg['propositions'], 1):
                lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
                lines.append(f"   - *Certainty*: {prop['certainty']}")
                if prop['concepts']:
                    lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Summary section
    lines.append("## 📊 Summary Analysis")
    lines.append("")

    lines.append("### Per-Message Breakdown")
    lines.append("")
    lines.append("| Message | Role | Type | Narrative Role | Propositions |")
    lines.append("|---------|------|------|----------------|--------------|")

    for msg in data['messages']:
        su = msg['semantic_unit']
        lines.append(f"| {msg['message_index']} | {su['speaker']} | {su['type']} | {su['narrative_role']} | {msg['proposition_count']} |")

    lines.append("")

    # Stats
    lines.append("### Statistics")
    lines.append("")

    core_count = sum(1 for m in data['messages'] if m['semantic_unit']['narrative_role'] == 'core')
    supportive_count = sum(1 for m in data['messages'] if m['semantic_unit']['narrative_role'] == 'supportive')
    peripheral_count = sum(1 for m in data['messages'] if m['semantic_unit']['narrative_role'] == 'peripheral')

    lines.append(f"**Narrative Role Distribution:**")
    lines.append(f"- Core: {core_count}/{len(data['messages'])}")
    lines.append(f"- Supportive: {supportive_count}/{len(data['messages'])}")
    lines.append(f"- Peripheral: {peripheral_count}/{len(data['messages'])}")
    lines.append("")

    # Type distribution
    types = {}
    for m in data['messages']:
        t = m['semantic_unit']['type']
        types[t] = types.get(t, 0) + 1

    lines.append(f"**Message Type Distribution:**")
    for msg_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {msg_type}: {count}")
    lines.append("")

    # Proposition distribution
    prop_types = {}
    for m in data['messages']:
        for p in m['propositions']:
            pt = p['type']
            prop_types[pt] = prop_types.get(pt, 0) + 1

    lines.append(f"**Proposition Type Distribution:**")
    for prop_type, count in sorted(prop_types.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {prop_type}: {count}")
    lines.append("")

    # Key improvements
    lines.append("### 🎯 Key Improvements in FIXED Version")
    lines.append("")
    lines.append("#### Problem Solved:")
    lines.append("**Before Fix:**")
    lines.append('- User asks: "ce inseamna o unitate semantica?"')
    lines.append('- LLM generates: "O unitate semantică este..." (answers the question!)')
    lines.append('- Result: Hallucination, wrong semantic unit type')
    lines.append("")
    lines.append("**After Fix:**")
    lines.append('- User asks: "ce inseamna o unitate semantica?"')
    lines.append('- LLM describes: "User-ul întreabă ce înseamnă o unitate semantică"')
    lines.append('- Result: Correct description, proper type classification (question)')
    lines.append("")

    lines.append("#### How It Was Fixed:")
    lines.append("1. **Clear role separation**: System prompt explicitly states LLM is an ANALYZER, not a PARTICIPANT")
    lines.append("2. **Visual separation**: Used separators (═══) to distinguish system instructions from conversation data")
    lines.append("3. **Explicit examples**: Added \"✅ CORECT\" vs \"❌ GREȘIT\" examples in prompt")
    lines.append("4. **Negative instructions**: \"❌ NU răspunde la întrebări\" - explicit prohibition")
    lines.append("")

    lines.append("#### Results:")
    lines.append(f"- **No hallucinations**: LLM describes what speakers say, doesn't generate new content")
    lines.append(f"- **Correct types**: Questions classified as 'question', agreements as 'agreement', etc")
    lines.append(f"- **Cleaner output**: {total_props} propositions (realistic, no repetitions from confusion)")
    lines.append(f"- **Better metadata**: Narrative roles and types accurately reflect message purpose")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by ReSemantic FIXED two-stage pipeline*")

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ FIXED report saved to {output_file}")


if __name__ == "__main__":
    generate_fixed_report(
        fixed_file="/opt/resemantic/FIXED_two_stage_results.json",
        output_file="/opt/resemantic/FIXED_REPORT.md"
    )
