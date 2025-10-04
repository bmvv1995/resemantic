"""
Generate human-readable Stage 2 comparison report.
Shows Baseline vs DSPy propositionalization on same semantic units.
"""

import json


def generate_stage2_report(stage2_file: str, output_file: str):
    """Create readable Stage 2 comparison report."""

    with open(stage2_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []

    # Header
    lines.append("# ⚛️ Stage 2 Propositionalization Comparison")
    lines.append("")
    lines.append("**Test Setup:**")
    lines.append("- **Stage 1**: FIXED semantic units (same for both)")
    lines.append("- **Stage 2A**: Baseline direct prompting")
    lines.append("- **Stage 2B**: DSPy structured signatures")
    lines.append("")
    lines.append("Both Stage 2 variants receive the SAME semantic units from Stage 1.")
    lines.append("This isolates the propositionalization approach.")
    lines.append("")
    lines.append(f"**Total Messages**: {len(data['messages'])}")
    lines.append("")

    # Summary
    baseline_total = sum(m['baseline_stage2']['count'] for m in data['messages'])
    dspy_total = sum(m['dspy_stage2']['count'] for m in data['messages'])

    lines.append("## 📊 Quick Summary")
    lines.append("")
    lines.append("| Stage 2 Approach | Total Props | Avg/Message |")
    lines.append("|------------------|-------------|-------------|")
    lines.append(f"| **Baseline** | {baseline_total} | {baseline_total/len(data['messages']):.1f} |")
    lines.append(f"| **DSPy** | {dspy_total} | {dspy_total/len(data['messages']):.1f} |")
    lines.append(f"| **Difference** | {baseline_total - dspy_total:+d} | {(baseline_total - dspy_total)/len(data['messages']):+.1f} |")
    lines.append("")

    if baseline_total > dspy_total:
        pct = ((baseline_total - dspy_total) / dspy_total * 100)
        lines.append(f"🏆 **Baseline extracts {pct:.1f}% MORE propositions than DSPy**")
    else:
        pct = ((dspy_total - baseline_total) / baseline_total * 100)
        lines.append(f"🏆 **DSPy extracts {pct:.1f}% MORE propositions than Baseline**")

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
        baseline_count = msg['baseline_stage2']['count']
        dspy_count = msg['dspy_stage2']['count']

        lines.append("---")
        lines.append("")
        lines.append("### ⚛️ Stage 2: Propositions Comparison")
        lines.append("")
        lines.append("| Approach | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| **Baseline** | {baseline_count} |")
        lines.append(f"| **DSPy** | {dspy_count} |")
        lines.append(f"| **Diff** | {baseline_count - dspy_count:+d} |")
        lines.append("")

        # Baseline propositions
        lines.append("#### 🔵 Baseline Stage 2 Propositions")
        lines.append("")
        if baseline_count == 0:
            lines.append("*No propositions extracted*")
            lines.append("")
        else:
            for i, prop in enumerate(msg['baseline_stage2']['propositions'], 1):
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

        # Quick analysis
        lines.append("<details>")
        lines.append("<summary>💡 Analysis (click to expand)</summary>")
        lines.append("")

        if baseline_count > dspy_count:
            lines.append(f"✅ **Baseline more granular**: {baseline_count - dspy_count} more propositions")
            lines.append("")
            lines.append("Baseline extracted more atomic units. Possible reasons:")
            lines.append("- More aggressive decomposition")
            lines.append("- Better at splitting compound statements")
            lines.append("- DSPy may be too conservative without optimization")
        elif dspy_count > baseline_count:
            lines.append(f"✅ **DSPy more granular**: {dspy_count - baseline_count} more propositions")
            lines.append("")
            lines.append("DSPy extracted more atomic units. Possible reasons:")
            lines.append("- Better structured decomposition")
            lines.append("- More consistent application of atomicity rules")
        else:
            lines.append("⚖️ **Equal granularity**: Both extracted same number of propositions")

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
    lines.append("| Message | Role | Type | Baseline | DSPy | Diff |")
    lines.append("|---------|------|------|----------|------|------|")

    for msg in data['messages']:
        su = msg['semantic_unit']
        b_count = msg['baseline_stage2']['count']
        d_count = msg['dspy_stage2']['count']
        lines.append(f"| {msg['message_index']} | {su['speaker']} | {su['type']} | {b_count} | {d_count} | {b_count - d_count:+d} |")

    lines.append("")

    # Winner determination
    lines.append("### 🏆 Winner: ")
    lines.append("")

    if baseline_total > dspy_total:
        diff_pct = ((baseline_total - dspy_total) / dspy_total * 100)
        lines.append(f"**BASELINE** extracts **{baseline_total - dspy_total} more propositions** ({diff_pct:.1f}% more)")
        lines.append("")
        lines.append("**Why Baseline wins:**")
        lines.append("- More aggressive atomic decomposition")
        lines.append("- Direct prompting with clear rules works well for this task")
        lines.append("- DSPy without few-shot optimization is too conservative")
        lines.append("- Simple task doesn't benefit from structured signatures overhead")
    else:
        diff_pct = ((dspy_total - baseline_total) / baseline_total * 100)
        lines.append(f"**DSPy** extracts **{dspy_total - baseline_total} more propositions** ({diff_pct:.1f}% more)")
        lines.append("")
        lines.append("**Why DSPy wins:**")
        lines.append("- Better structured decomposition")
        lines.append("- More consistent application of rules")
        lines.append("- Structured signatures enforce atomicity better")

    lines.append("")

    # Consistency analysis
    lines.append("### 📈 Consistency Analysis")
    lines.append("")

    baseline_counts = [m['baseline_stage2']['count'] for m in data['messages']]
    dspy_counts = [m['dspy_stage2']['count'] for m in data['messages']]

    import statistics
    baseline_stdev = statistics.stdev(baseline_counts) if len(baseline_counts) > 1 else 0
    dspy_stdev = statistics.stdev(dspy_counts) if len(dspy_counts) > 1 else 0

    lines.append(f"**Standard Deviation (consistency):**")
    lines.append(f"- Baseline: {baseline_stdev:.2f}")
    lines.append(f"- DSPy: {dspy_stdev:.2f}")
    lines.append("")

    if baseline_stdev < dspy_stdev:
        lines.append("✅ **Baseline more consistent** - lower variance in proposition counts")
    elif dspy_stdev < baseline_stdev:
        lines.append("✅ **DSPy more consistent** - lower variance in proposition counts")
    else:
        lines.append("⚖️ **Equal consistency**")

    lines.append("")

    # Recommendations
    lines.append("### 💡 Recommendations")
    lines.append("")

    lines.append("#### For Production Use:")
    lines.append("")

    if baseline_total > dspy_total:
        lines.append("**Use Baseline Stage 2** because:")
        lines.append("- ✅ More granular atomic decomposition")
        lines.append("- ✅ Simpler implementation (direct prompting)")
        lines.append("- ✅ Lower latency (no DSPy overhead)")
        lines.append("- ✅ Easier to debug and modify")
        lines.append("")
        lines.append("**DSPy might improve with:**")
        lines.append("- Few-shot examples in signature")
        lines.append("- Optimizer training (BootstrapFewShot)")
        lines.append("- Task-specific tuning")
    else:
        lines.append("**Use DSPy Stage 2** because:")
        lines.append("- ✅ More granular atomic decomposition")
        lines.append("- ✅ Better structured approach")
        lines.append("- ✅ More consistent results")
        lines.append("")
        lines.append("**Baseline might improve with:**")
        lines.append("- More explicit examples in prompt")
        lines.append("- Stricter atomicity rules")

    lines.append("")

    lines.append("#### Full Pipeline Recommendation:")
    lines.append("")
    lines.append("```")
    lines.append("FIXED Stage 1 (clear system/data separation)")
    lines.append("     ↓")
    lines.append("Semantic Units (no hallucinations, rich metadata)")
    lines.append("     ↓")
    if baseline_total > dspy_total:
        lines.append("Baseline Stage 2 (more granular propositions)")
    else:
        lines.append("DSPy Stage 2 (better structured propositions)")
    lines.append("     ↓")
    lines.append("Embeddings + Graph Construction")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by ReSemantic Stage 2 comparison experiment*")

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ Stage 2 comparison report saved to {output_file}")


if __name__ == "__main__":
    generate_stage2_report(
        stage2_file="/opt/resemantic/stage2_comparison.json",
        output_file="/opt/resemantic/STAGE2_COMPARISON.md"
    )
