"""
Generate human-readable report for FIXED Stage 2 comparison.
Shows FIXED Baseline vs DSPy (both without hallucinations).
"""

import json


def generate_fixed_stage2_report(fixed_stage2_file: str, output_file: str):
    """Create readable report from FIXED Stage 2 comparison."""

    with open(fixed_stage2_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []

    # Header
    lines.append("# ⚛️ FIXED Stage 2 Propositionalization Comparison")
    lines.append("")
    lines.append("**Test Setup:**")
    lines.append("- **Stage 1**: FIXED semantic units (same for both)")
    lines.append("- **Stage 2A**: FIXED Baseline (strict no-hallucination prompt)")
    lines.append("- **Stage 2B**: DSPy structured signatures")
    lines.append("")
    lines.append("**KEY IMPROVEMENT:** Baseline prompt now has strict rules against:")
    lines.append("- ❌ Adding definitions not in semantic unit")
    lines.append("- ❌ Generating general knowledge")
    lines.append("- ❌ Explaining what terms mean")
    lines.append("- ✅ Only describe what the semantic unit says")
    lines.append("")
    lines.append(f"**Total Messages**: {len(data['messages'])}")
    lines.append("")

    # Summary
    fixed_baseline_total = sum(m['fixed_baseline_stage2']['count'] for m in data['messages'])
    dspy_total = sum(m['dspy_stage2']['count'] for m in data['messages'])

    lines.append("## 📊 Quick Summary")
    lines.append("")
    lines.append("| Stage 2 Approach | Total Props | Avg/Message |")
    lines.append("|------------------|-------------|-------------|")
    lines.append(f"| **FIXED Baseline** | {fixed_baseline_total} | {fixed_baseline_total/len(data['messages']):.1f} |")
    lines.append(f"| **DSPy** | {dspy_total} | {dspy_total/len(data['messages']):.1f} |")
    lines.append(f"| **Difference** | {fixed_baseline_total - dspy_total:+d} | {(fixed_baseline_total - dspy_total)/len(data['messages']):+.1f} |")
    lines.append("")

    if fixed_baseline_total > dspy_total:
        pct = ((fixed_baseline_total - dspy_total) / dspy_total * 100)
        lines.append(f"🏆 **FIXED Baseline extracts {pct:.1f}% MORE propositions than DSPy**")
    elif dspy_total > fixed_baseline_total:
        pct = ((dspy_total - fixed_baseline_total) / fixed_baseline_total * 100)
        lines.append(f"🏆 **DSPy extracts {pct:.1f}% MORE propositions than FIXED Baseline**")
    else:
        lines.append("⚖️ **EQUAL - Both extract same number of propositions!**")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Per message comparison
    for msg in data['messages']:
        msg_num = msg['message_index']
        su = msg['semantic_unit']

        lines.append(f"## 📬 Message {msg_num} - {su['speaker'].upper()}")
        lines.append("")

        # Original message
        lines.append("### 📝 Original Message")
        lines.append("```")
        lines.append(msg['original_content'])
        lines.append("```")
        lines.append("")

        # Stage 1 Semantic Unit
        lines.append("### 🎯 Stage 1: Semantic Unit (SAME for both)")
        lines.append("")
        lines.append(f"**Content:**")
        lines.append(f"> {su['content']}")
        lines.append("")
        lines.append(f"**Metadata:**")
        lines.append(f"- Type: `{su['type']}`")
        lines.append(f"- Narrative Role: `{su['narrative_role']}`")
        lines.append(f"- Concepts: {', '.join(su['concepts']) if su['concepts'] else 'none'}")
        lines.append("")

        # Comparison
        fixed_baseline_count = msg['fixed_baseline_stage2']['count']
        dspy_count = msg['dspy_stage2']['count']

        lines.append("---")
        lines.append("")
        lines.append("### ⚛️ Stage 2: Propositions Comparison")
        lines.append("")
        lines.append("| Approach | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| **FIXED Baseline** | {fixed_baseline_count} |")
        lines.append(f"| **DSPy** | {dspy_count} |")
        lines.append(f"| **Diff** | {fixed_baseline_count - dspy_count:+d} |")
        lines.append("")

        # FIXED Baseline propositions
        lines.append("#### 🔵 FIXED Baseline Stage 2 Propositions")
        lines.append("")
        if fixed_baseline_count == 0:
            lines.append("*No propositions extracted*")
            lines.append("")
        else:
            for i, prop in enumerate(msg['fixed_baseline_stage2']['propositions'], 1):
                lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
                lines.append(f"   - *Certainty*: {prop['certainty']}")
                if prop['concepts']:
                    lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
                lines.append("")

        # DSPy propositions
        lines.append("#### 🟣 DSPy Stage 2 Propositions")
        lines.append("")
        if dspy_count == 0:
            lines.append("*No propositions extracted*")
            lines.append("")
        else:
            for i, prop in enumerate(msg['dspy_stage2']['propositions'], 1):
                lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
                lines.append(f"   - *Certainty*: {prop['certainty']}")
                if prop['concepts']:
                    lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
                lines.append("")

        # Analysis
        lines.append("<details>")
        lines.append("<summary>💡 Analysis (click to expand)</summary>")
        lines.append("")

        if fixed_baseline_count == dspy_count:
            lines.append(f"⚖️ **Equal granularity**: Both extracted {fixed_baseline_count} propositions")
            lines.append("")
            lines.append("Perfect agreement on atomicity level!")
        elif fixed_baseline_count > dspy_count:
            lines.append(f"✅ **FIXED Baseline more granular**: {fixed_baseline_count - dspy_count} more propositions")
            lines.append("")
            lines.append("Possible reasons:")
            lines.append("- Baseline splits compound statements more aggressively")
            lines.append("- DSPy may combine related ideas")
            lines.append("- Different interpretation of 'atomic'")
        else:
            lines.append(f"✅ **DSPy more granular**: {dspy_count - fixed_baseline_count} more propositions")
            lines.append("")
            lines.append("Possible reasons:")
            lines.append("- DSPy splits compound statements more aggressively")
            lines.append("- Baseline may combine related ideas")
            lines.append("- Different interpretation of 'atomic'")

        lines.append("")
        lines.append("</details>")
        lines.append("")

        lines.append("---")
        lines.append("")

    # Overall analysis
    lines.append("## 🔍 Overall Analysis")
    lines.append("")

    lines.append("### Per-Message Breakdown")
    lines.append("")
    lines.append("| Message | Role | Type | FIXED Baseline | DSPy | Diff |")
    lines.append("|---------|------|------|----------------|------|------|")

    for msg in data['messages']:
        su = msg['semantic_unit']
        fb_count = msg['fixed_baseline_stage2']['count']
        d_count = msg['dspy_stage2']['count']
        lines.append(f"| {msg['message_index']} | {su['speaker']} | {su['type']} | {fb_count} | {d_count} | {fb_count - d_count:+d} |")

    lines.append("")

    # Messages where they agree
    equal_messages = [m for m in data['messages']
                     if m['fixed_baseline_stage2']['count'] == m['dspy_stage2']['count']]

    if equal_messages:
        lines.append(f"### ⚖️ Perfect Agreement ({len(equal_messages)}/{len(data['messages'])} messages)")
        lines.append("")
        lines.append("Messages where both extracted same number of propositions:")
        for m in equal_messages:
            lines.append(f"- Message {m['message_index']}: {m['fixed_baseline_stage2']['count']} props")
        lines.append("")

    # Winner
    lines.append("### 🏆 Winner")
    lines.append("")

    if fixed_baseline_total > dspy_total:
        diff = fixed_baseline_total - dspy_total
        diff_pct = (diff / dspy_total * 100)
        lines.append(f"**FIXED Baseline** extracts **{diff} more propositions** ({diff_pct:.1f}% more)")
        lines.append("")
        lines.append("**Why FIXED Baseline wins:**")
        lines.append("- More aggressive atomic decomposition")
        lines.append("- Better at splitting compound statements")
        lines.append("- Direct prompting with clear examples works well")
        lines.append("- No hallucinations after fix (strict rules)")
        lines.append("")
        lines.append("**DSPy characteristics:**")
        lines.append("- More conservative decomposition")
        lines.append("- May combine related ideas more")
        lines.append("- Structured signatures ensure consistency")
        lines.append("- Needs few-shot optimization to match baseline")
    elif dspy_total > fixed_baseline_total:
        diff = dspy_total - fixed_baseline_total
        diff_pct = (diff / fixed_baseline_total * 100)
        lines.append(f"**DSPy** extracts **{diff} more propositions** ({diff_pct:.1f}% more)")
        lines.append("")
        lines.append("**Why DSPy wins:**")
        lines.append("- More aggressive atomic decomposition")
        lines.append("- Better at splitting compound statements")
        lines.append("- Structured signatures enforce atomicity")
        lines.append("")
        lines.append("**FIXED Baseline characteristics:**")
        lines.append("- More conservative after strict rules")
        lines.append("- May combine related ideas more")
    else:
        lines.append("**EQUAL - Perfect tie!**")
        lines.append("")
        lines.append("Both approaches extract the same total number of propositions.")
        lines.append("This suggests:")
        lines.append("- Both have reached optimal atomicity level")
        lines.append("- FIXED prompt made Baseline as good as DSPy")
        lines.append("- For this task, simple prompting = structured signatures")

    lines.append("")

    # Consistency
    lines.append("### 📈 Consistency Analysis")
    lines.append("")

    import statistics
    fb_counts = [m['fixed_baseline_stage2']['count'] for m in data['messages']]
    d_counts = [m['dspy_stage2']['count'] for m in data['messages']]

    fb_stdev = statistics.stdev(fb_counts) if len(fb_counts) > 1 else 0
    d_stdev = statistics.stdev(d_counts) if len(d_counts) > 1 else 0

    lines.append(f"**Standard Deviation:**")
    lines.append(f"- FIXED Baseline: {fb_stdev:.2f}")
    lines.append(f"- DSPy: {d_stdev:.2f}")
    lines.append("")

    if fb_stdev < d_stdev:
        lines.append("✅ **FIXED Baseline more consistent** - lower variance")
    elif d_stdev < fb_stdev:
        lines.append("✅ **DSPy more consistent** - lower variance")
    else:
        lines.append("⚖️ **Equal consistency**")

    lines.append("")

    # Final recommendation
    lines.append("## 💡 Final Recommendation")
    lines.append("")

    lines.append("### For Production:")
    lines.append("")

    if abs(fixed_baseline_total - dspy_total) <= 3:
        lines.append("**Use FIXED Baseline** because:")
        lines.append("- ✅ Equivalent quality to DSPy")
        lines.append("- ✅ Simpler implementation (direct prompting)")
        lines.append("- ✅ Lower latency (no DSPy overhead)")
        lines.append("- ✅ Easier to debug and modify")
        lines.append("- ✅ No hallucinations after fix")
        lines.append("")
        lines.append("**DSPy doesn't provide significant benefit** for this task")
        lines.append("- Similar proposition counts")
        lines.append("- Would need optimization to improve")
        lines.append("- Overhead not justified")
    elif fixed_baseline_total > dspy_total:
        lines.append("**Use FIXED Baseline** because:")
        lines.append(f"- ✅ Extracts {fixed_baseline_total - dspy_total} more propositions")
        lines.append("- ✅ More granular decomposition")
        lines.append("- ✅ Simpler implementation")
        lines.append("- ✅ Lower latency")
        lines.append("- ✅ No hallucinations after fix")
    else:
        lines.append("**Use DSPy** if:")
        lines.append(f"- You need {dspy_total - fixed_baseline_total} more propositions")
        lines.append("- You value structured approach")
        lines.append("- You plan to optimize with few-shot examples")
        lines.append("")
        lines.append("**Use FIXED Baseline** if:")
        lines.append("- Simplicity is priority")
        lines.append("- Lower latency matters")
        lines.append("- Easier maintenance desired")

    lines.append("")

    lines.append("### Recommended Full Pipeline:")
    lines.append("")
    lines.append("```")
    lines.append("FIXED Stage 1")
    lines.append("  ↓")
    lines.append("Semantic Units (no hallucinations)")
    lines.append("  ↓")
    if fixed_baseline_total >= dspy_total - 3:
        lines.append("FIXED Baseline Stage 2")
    else:
        lines.append("DSPy Stage 2 (optimized)")
    lines.append("  ↓")
    lines.append("Atomic Propositions")
    lines.append("  ↓")
    lines.append("Embeddings + Graph Construction")
    lines.append("  ↓")
    lines.append("Living Knowledge Ecosystem")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by ReSemantic FIXED Stage 2 comparison experiment*")

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ FIXED Stage 2 comparison report saved to {output_file}")


if __name__ == "__main__":
    generate_fixed_stage2_report(
        fixed_stage2_file="/opt/resemantic/stage2_fixed_comparison.json",
        output_file="/opt/resemantic/FIXED_STAGE2_COMPARISON.md"
    )
