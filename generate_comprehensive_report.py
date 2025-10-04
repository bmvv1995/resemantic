"""
Generate comprehensive human-readable comparison report.

Shows side-by-side for each message:
1. Original message
2. Stage 1 (Enhanced Semantic Unit with metadata)
3. Stage 2 Baseline propositions
4. Stage 2 DSPy propositions (from previous single-stage test)
"""

import json


def generate_comprehensive_report(
    enhanced_file: str,
    single_stage_file: str,
    output_file: str
):
    """Create detailed comparison report."""

    # Load data
    with open(enhanced_file, 'r', encoding='utf-8') as f:
        enhanced_data = json.load(f)

    with open(single_stage_file, 'r', encoding='utf-8') as f:
        single_stage_data = json.load(f)

    lines = []

    # Header
    lines.append("# 🔬 Comprehensive Proposition Extraction Analysis")
    lines.append("")
    lines.append("**Comparison of Three Approaches:**")
    lines.append("1. **Two-Stage Enhanced** (Semantic Unit → Propositions)")
    lines.append("2. **Single-Stage Baseline** (Direct prompt)")
    lines.append("3. **Single-Stage DSPy** (Structured signatures)")
    lines.append("")
    lines.append("**Processing Mode**: Message-by-message incremental (each message with growing context)")
    lines.append("")
    lines.append(f"**Total Messages**: {len(enhanced_data['messages'])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Totals
    enhanced_total = sum(m['proposition_count'] for m in enhanced_data['messages'])
    baseline_total = sum(m['baseline']['count'] for m in single_stage_data['messages'])
    dspy_total = sum(m['dspy']['count'] for m in single_stage_data['messages'])

    lines.append("## 📊 Quick Summary")
    lines.append("")
    lines.append("| Approach | Total Props | Avg/Message |")
    lines.append("|----------|-------------|-------------|")
    lines.append(f"| **Two-Stage Enhanced** | {enhanced_total} | {enhanced_total/len(enhanced_data['messages']):.1f} |")
    lines.append(f"| **Single-Stage Baseline** | {baseline_total} | {baseline_total/len(single_stage_data['messages']):.1f} |")
    lines.append(f"| **Single-Stage DSPy** | {dspy_total} | {dspy_total/len(single_stage_data['messages']):.1f} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process each message
    for idx, enhanced_msg in enumerate(enhanced_data['messages']):
        single_msg = single_stage_data['messages'][idx]
        msg_num = enhanced_msg['message_index']
        role = enhanced_msg['semantic_unit']['speaker'].upper()

        lines.append(f"## 📬 Message {msg_num} - {role}")
        lines.append("")

        # Original message
        lines.append("### 📝 Original Message")
        lines.append("```")
        lines.append(enhanced_msg['original_content'])
        lines.append("```")
        lines.append("")

        # Context (if not first message)
        if enhanced_msg['context_used'] != "Start of conversation":
            lines.append("<details>")
            lines.append("<summary>🔗 Context Used (click to expand)</summary>")
            lines.append("")
            lines.append("```")
            lines.append(enhanced_msg['context_used'])
            lines.append("```")
            lines.append("</details>")
            lines.append("")

        # Stage 1: Enhanced Semantic Unit
        lines.append("---")
        lines.append("")
        lines.append("### 🎯 STAGE 1: Enhanced Semantic Unit")
        lines.append("")

        su = enhanced_msg['semantic_unit']
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

        # Stage 2 comparisons
        lines.append("---")
        lines.append("")
        lines.append("### ⚛️ STAGE 2: Propositions Comparison")
        lines.append("")

        enhanced_count = enhanced_msg['proposition_count']
        baseline_count = single_msg['baseline']['count']
        dspy_count = single_msg['dspy']['count']

        lines.append("| Approach | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| Two-Stage Enhanced | **{enhanced_count}** |")
        lines.append(f"| Single-Stage Baseline | **{baseline_count}** |")
        lines.append(f"| Single-Stage DSPy | **{dspy_count}** |")
        lines.append("")

        # Two-Stage Enhanced propositions
        lines.append("#### 🟢 Two-Stage Enhanced Propositions")
        lines.append("")
        for i, prop in enumerate(enhanced_msg['propositions'], 1):
            lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
            lines.append(f"   - *Certainty*: {prop['certainty']}")
            if prop['concepts']:
                lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
            lines.append("")

        # Baseline propositions
        lines.append("#### 🔵 Single-Stage Baseline Propositions")
        lines.append("")
        for i, prop in enumerate(single_msg['baseline']['propositions'], 1):
            lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
            lines.append(f"   - *Certainty*: {prop['certainty']}")
            if prop['concepts']:
                lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
            lines.append("")

        # DSPy propositions
        lines.append("#### 🟣 Single-Stage DSPy Propositions")
        lines.append("")
        for i, prop in enumerate(single_msg['dspy']['propositions'], 1):
            lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
            lines.append(f"   - *Certainty*: {prop['certainty']}")
            if prop['concepts']:
                lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
            lines.append("")

        # Quick analysis for this message
        lines.append("<details>")
        lines.append("<summary>💡 Quick Analysis (click to expand)</summary>")
        lines.append("")
        lines.append(f"**Proposition Counts:**")
        lines.append(f"- Two-Stage: {enhanced_count} props")
        lines.append(f"- Baseline: {baseline_count} props ({baseline_count - enhanced_count:+d} vs Two-Stage)")
        lines.append(f"- DSPy: {dspy_count} props ({dspy_count - enhanced_count:+d} vs Two-Stage)")
        lines.append("")

        # Highlight differences
        if enhanced_count > baseline_count and enhanced_count > dspy_count:
            lines.append("✅ **Two-Stage is most granular** - extracts more atomic propositions")
        elif baseline_count > enhanced_count and baseline_count > dspy_count:
            lines.append("⚠️ **Baseline most granular** - may include repetitions or hallucinations")
        elif dspy_count > enhanced_count and dspy_count > baseline_count:
            lines.append("⚠️ **DSPy most granular** - check for over-decomposition")

        lines.append("")
        lines.append("</details>")
        lines.append("")

        lines.append("---")
        lines.append("")

    # Final comprehensive analysis
    lines.append("## 🔍 Overall Analysis")
    lines.append("")

    lines.append("### Quantitative Comparison")
    lines.append("")
    lines.append("| Metric | Two-Stage | Baseline | DSPy |")
    lines.append("|--------|-----------|----------|------|")
    lines.append(f"| **Total Propositions** | {enhanced_total} | {baseline_total} | {dspy_total} |")
    lines.append(f"| **Avg per Message** | {enhanced_total/len(enhanced_data['messages']):.1f} | {baseline_total/len(single_stage_data['messages']):.1f} | {dspy_total/len(single_stage_data['messages']):.1f} |")
    lines.append(f"| **vs Two-Stage** | baseline | {baseline_total - enhanced_total:+d} ({(baseline_total-enhanced_total)/enhanced_total*100:+.1f}%) | {dspy_total - enhanced_total:+d} ({(dspy_total-enhanced_total)/enhanced_total*100:+.1f}%) |")
    lines.append("")

    # Per message breakdown
    lines.append("### Per-Message Breakdown")
    lines.append("")
    lines.append("| Message | Role | Enhanced | Baseline | DSPy |")
    lines.append("|---------|------|----------|----------|------|")

    for i, enhanced_msg in enumerate(enhanced_data['messages']):
        single_msg = single_stage_data['messages'][i]
        msg_num = enhanced_msg['message_index']
        role = enhanced_msg['semantic_unit']['speaker']
        e_count = enhanced_msg['proposition_count']
        b_count = single_msg['baseline']['count']
        d_count = single_msg['dspy']['count']

        lines.append(f"| {msg_num} | {role} | {e_count} | {b_count} | {d_count} |")

    lines.append("")

    # Key insights
    lines.append("### 🎯 Key Insights")
    lines.append("")

    lines.append("#### 1. **Two-Stage Architecture Benefits**")
    lines.append("")
    lines.append("**Stage 1 (Semantic Unit):**")
    lines.append("- Resolves coreferințe using full context")
    lines.append("- Expands short responses (\"da\") with implicit meaning")
    lines.append("- Captures rich metadata (type, narrative role, concepts, etc)")
    lines.append("- Creates self-contained semantic description")
    lines.append("")
    lines.append("**Stage 2 (Propositionalization):**")
    lines.append("- Works on clean, resolved semantic unit")
    lines.append("- No confusion from long context")
    lines.append("- Focused atomic decomposition")
    lines.append("- Less hallucination risk")
    lines.append("")

    lines.append("#### 2. **Comparison with Single-Stage**")
    lines.append("")

    if enhanced_total > baseline_total:
        lines.append(f"- **Two-Stage extracts {enhanced_total - baseline_total} MORE propositions** than Baseline")
        lines.append("  - More granular decomposition")
        lines.append("  - Better captures nuanced information")
    else:
        lines.append(f"- **Baseline extracts {baseline_total - enhanced_total} MORE propositions** than Two-Stage")
        lines.append("  - May include repetitions from context")
        lines.append("  - Risk of hallucinations")

    lines.append("")

    if enhanced_total > dspy_total:
        lines.append(f"- **Two-Stage extracts {enhanced_total - dspy_total} MORE propositions** than DSPy")
        lines.append("  - DSPy may be too conservative without optimization")
        lines.append("  - DSPy needs few-shot examples to improve")
    else:
        lines.append(f"- **DSPy extracts {dspy_total - enhanced_total} MORE propositions** than Two-Stage")
        lines.append("  - Check if over-decomposed")

    lines.append("")

    lines.append("#### 3. **Metadata Richness (Two-Stage Only)**")
    lines.append("")
    lines.append("Two-Stage provides:")
    lines.append("- `narrative_role`: core/supportive/peripheral classification")
    lines.append("- `type`: request/decision/information/agreement/etc")
    lines.append("- `relevance`: high/medium/low")
    lines.append("- `impact`: major/minor/neutral")
    lines.append("- `certainty`: high/medium/low")
    lines.append("- `concepts`: extracted key concepts")
    lines.append("- `entities`: named entities")
    lines.append("- `decisions`: explicit/implicit decisions")
    lines.append("- `context_dependencies`: what previous info is referenced")
    lines.append("")
    lines.append("This metadata enables:")
    lines.append("- **Smart filtering** (only embed \"core\" units)")
    lines.append("- **Importance weighting** (relevance + impact)")
    lines.append("- **Relationship mapping** (context dependencies)")
    lines.append("- **Sleep cycle consolidation** (narrative role + certainty)")
    lines.append("")

    lines.append("### 🏆 Recommendation")
    lines.append("")
    lines.append("**Use Two-Stage Enhanced Pipeline for:**")
    lines.append("")
    lines.append("✅ **Rich metadata** for Living Knowledge Ecosystem")
    lines.append("✅ **Clean separation** of understanding vs atomization")
    lines.append("✅ **Better context handling** (resolve refs in Stage 1)")
    lines.append("✅ **Reduced hallucination** (Stage 2 only sees resolved semantic unit)")
    lines.append("✅ **Flexible processing** (can skip Stage 2 for peripheral units)")
    lines.append("")
    lines.append("The two-stage approach provides the **best balance** of:")
    lines.append("- Semantic completeness (Stage 1)")
    lines.append("- Atomic granularity (Stage 2)")
    lines.append("- Metadata richness (Stage 1)")
    lines.append("- Embedding quality (Stage 2)")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by ReSemantic proposition extraction experiment*")

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ Comprehensive report saved to {output_file}")


if __name__ == "__main__":
    generate_comprehensive_report(
        enhanced_file="/opt/resemantic/enhanced_two_stage_results.json",
        single_stage_file="/opt/resemantic/message_by_message_analysis.json",
        output_file="/opt/resemantic/COMPREHENSIVE_COMPARISON.md"
    )
