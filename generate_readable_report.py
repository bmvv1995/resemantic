"""
Generate human-readable side-by-side comparison report.
"""

import json


def generate_report(analysis_file: str, output_file: str):
    """Create readable markdown report from analysis."""

    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []

    lines.append("# 📊 Message-by-Message Proposition Analysis")
    lines.append("")
    lines.append("**Processing Mode**: Incremental (each message processed individually with growing context)")
    lines.append("")
    lines.append(f"**Total Messages**: {data['metadata']['total_messages']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    baseline_total = 0
    dspy_total = 0

    for msg in data['messages']:
        idx = msg['message_index']
        role = msg['role'].upper()

        lines.append(f"## Message {idx} - {role}")
        lines.append("")

        # Original content
        lines.append("### 📝 Original Message:")
        lines.append("```")
        lines.append(msg['original_content'])
        lines.append("```")
        lines.append("")

        # Context used
        if msg['context_used'] != "Start of conversation":
            lines.append("### 🔗 Context Used:")
            lines.append("```")
            lines.append(msg['context_used'])
            lines.append("```")
            lines.append("")

        baseline_count = msg['baseline']['count']
        dspy_count = msg['dspy']['count']

        baseline_total += baseline_count
        dspy_total += dspy_count

        # Summary
        lines.append(f"### 📈 Extraction Summary:")
        lines.append(f"- **Baseline**: {baseline_count} propositions")
        lines.append(f"- **DSPy**: {dspy_count} propositions")
        lines.append(f"- **Difference**: {baseline_count - dspy_count:+d}")
        lines.append("")

        # Side by side propositions
        lines.append("### 🔵 Baseline Propositions:")
        lines.append("")
        for i, prop in enumerate(msg['baseline']['propositions'], 1):
            lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
            lines.append(f"   - *Certainty*: {prop['certainty']}")
            lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
            lines.append("")

        lines.append("### 🟢 DSPy Propositions:")
        lines.append("")
        for i, prop in enumerate(msg['dspy']['propositions'], 1):
            lines.append(f"{i}. **[{prop['type']}]** {prop['content']}")
            lines.append(f"   - *Certainty*: {prop['certainty']}")
            lines.append(f"   - *Concepts*: {', '.join(prop['concepts'])}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Final summary
    lines.append("## 📊 FINAL SUMMARY")
    lines.append("")
    lines.append("| Metric | Baseline | DSPy | Difference |")
    lines.append("|--------|----------|------|------------|")
    lines.append(f"| **Total Propositions** | {baseline_total} | {dspy_total} | {baseline_total - dspy_total:+d} |")
    lines.append(f"| **Avg per Message** | {baseline_total / data['metadata']['total_messages']:.1f} | {dspy_total / data['metadata']['total_messages']:.1f} | {(baseline_total - dspy_total) / data['metadata']['total_messages']:+.1f} |")
    lines.append("")

    # Per message breakdown
    lines.append("### Per-Message Breakdown:")
    lines.append("")
    lines.append("| Message | Role | Baseline | DSPy | Diff |")
    lines.append("|---------|------|----------|------|------|")
    for msg in data['messages']:
        b_count = msg['baseline']['count']
        d_count = msg['dspy']['count']
        lines.append(f"| {msg['message_index']} | {msg['role']} | {b_count} | {d_count} | {b_count - d_count:+d} |")
    lines.append("")

    # Analysis
    lines.append("## 🔍 Key Observations")
    lines.append("")

    # Find biggest differences
    diffs = [(msg['message_index'], msg['role'], msg['baseline']['count'] - msg['dspy']['count'])
             for msg in data['messages']]
    diffs.sort(key=lambda x: abs(x[2]), reverse=True)

    lines.append("### Largest Differences:")
    for idx, role, diff in diffs[:3]:
        lines.append(f"- **Message {idx} ({role})**: {diff:+d} propositions")
    lines.append("")

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ Readable report saved to {output_file}")


if __name__ == "__main__":
    generate_report(
        analysis_file="/opt/resemantic/message_by_message_analysis.json",
        output_file="/opt/resemantic/MESSAGE_BY_MESSAGE_COMPARISON.md"
    )
