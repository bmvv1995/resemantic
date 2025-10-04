"""
Compare Stage 2 approaches: Baseline vs DSPy
Both use the SAME Stage 1 semantic units from FIXED pipeline.
"""

import json
import dspy
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import os


@dataclass
class Proposition:
    content: str
    type: str
    certainty: str
    concepts: List[str]


class BaselineStage2:
    """Baseline propositionalization (direct prompting)."""

    def __init__(self, lm):
        self.lm = lm

    def propositionalize(self, semantic_unit: Dict) -> List[Proposition]:
        """Break semantic unit into propositions with direct prompt."""

        prompt = f"""Descompune această unitate semantică în propoziții atomice pentru embeddings.

Unitate semantică:
{semantic_unit['content']}

Concepte principale: {', '.join(semantic_unit['concepts'])}
Type: {semantic_unit['type']}
Narrative role: {semantic_unit['narrative_role']}

Reguli:
- Fiecare propoziție = UN fapt/opinie/afirmație atomică
- Fiecare propoziție trebuie să fie auto-suficientă
- NU adăuga informație nouă
- NU repeta aceeași informație
- Păstrează nuanțe (certitudine, opinie vs fapt)
- Pentru "supportive"/"peripheral": maxim 2-3 propositions
- Pentru "core": toate propozițiile atomice necesare

Returnează JSON:
[
  {{
    "content": "propoziție atomică",
    "type": "fact|opinion|question|agreement|decision",
    "certainty": "high|medium|low",
    "concepts": ["concepte"]
  }}
]
"""

        response = self.lm(prompt)
        response_text = self._extract_text(response)
        response_text = self._strip_markdown(response_text)

        try:
            props_data = json.loads(response_text)
            return [
                Proposition(
                    content=p['content'],
                    type=p.get('type', 'fact'),
                    certainty=p.get('certainty', 'medium'),
                    concepts=p.get('concepts', [])
                )
                for p in props_data
            ]
        except Exception as e:
            print(f"Baseline Stage 2 error: {e}")
            return []

    def _extract_text(self, response):
        if isinstance(response, list) and len(response) > 0:
            return response[0]
        elif isinstance(response, str):
            return response
        elif hasattr(response, 'choices'):
            return response.choices[0].message.content
        return str(response)

    def _strip_markdown(self, text: str) -> str:
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return text.strip()


class DSPyStage2(dspy.Module):
    """DSPy propositionalization (structured signatures)."""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(PropositionSignature)

    def propositionalize(self, semantic_unit: Dict) -> List[Proposition]:
        """Break semantic unit into propositions with DSPy."""

        result = self.extract(
            semantic_unit_content=semantic_unit['content'],
            concepts=', '.join(semantic_unit['concepts']),
            unit_type=semantic_unit['type'],
            narrative_role=semantic_unit['narrative_role']
        )

        try:
            if isinstance(result.propositions, str):
                props_data = json.loads(result.propositions)
            elif isinstance(result.propositions, list):
                props_data = result.propositions
            else:
                props_data = [result.propositions]

            return [
                Proposition(
                    content=p.get('content', str(p)),
                    type=p.get('type', 'fact'),
                    certainty=p.get('certainty', 'medium'),
                    concepts=p.get('concepts', [])
                )
                for p in props_data
            ]
        except Exception as e:
            print(f"DSPy Stage 2 error: {e}")
            return []


class PropositionSignature(dspy.Signature):
    """Extract atomic propositions from semantic unit."""

    semantic_unit_content: str = dspy.InputField(desc="The semantic unit to decompose")
    concepts: str = dspy.InputField(desc="Main concepts in the unit")
    unit_type: str = dspy.InputField(desc="Type of the unit")
    narrative_role: str = dspy.InputField(desc="Narrative role: core/supportive/peripheral")

    propositions: List[Dict[str, Any]] = dspy.OutputField(
        desc="""List of atomic propositions in JSON format:
        [
          {
            "content": "self-contained atomic statement",
            "type": "fact|opinion|question|agreement|decision",
            "certainty": "high|medium|low",
            "concepts": ["key", "concepts"]
          }
        ]

        Rules:
        - Each proposition = ONE atomic fact/opinion/statement
        - Must be self-contained (understandable independently)
        - NO new information not in semantic unit
        - NO repetition
        - For supportive/peripheral: max 2-3 propositions
        - For core: all necessary atomic propositions
        """
    )


def run_stage2_comparison(fixed_results_file: str, api_key: str, output_file: str):
    """Compare Baseline vs DSPy for Stage 2 propositionalization."""

    print("🔧 Setting up Stage 2 comparison...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    baseline_stage2 = BaselineStage2(lm)
    dspy_stage2 = DSPyStage2()

    # Load FIXED Stage 1 results
    with open(fixed_results_file, 'r', encoding='utf-8') as f:
        fixed_data = json.load(f)

    print(f"📖 Processing {len(fixed_data['messages'])} semantic units through Stage 2...\n")

    results = {
        "metadata": {
            "test": "Stage 2 comparison (Baseline vs DSPy)",
            "stage_1": "FIXED semantic units (same for both)",
            "stage_2a": "Baseline direct prompting",
            "stage_2b": "DSPy structured signatures",
            "total_messages": len(fixed_data['messages'])
        },
        "messages": []
    }

    # Process each semantic unit through both Stage 2 variants
    for msg in fixed_data['messages']:
        msg_num = msg['message_index']
        su = msg['semantic_unit']

        print(f"{'='*70}")
        print(f"MESSAGE {msg_num} - {su['speaker'].upper()}")
        print(f"{'='*70}")
        print(f"Semantic Unit: {su['content'][:80]}...")

        # Baseline Stage 2
        print("\n🔵 Baseline Stage 2...")
        baseline_props = baseline_stage2.propositionalize(su)
        print(f"   → {len(baseline_props)} propositions")

        # DSPy Stage 2
        print("🟣 DSPy Stage 2...")
        dspy_props = dspy_stage2.propositionalize(su)
        print(f"   → {len(dspy_props)} propositions")
        print()

        # Store
        message_result = {
            "message_index": msg_num,
            "original_content": msg['original_content'],
            "semantic_unit": su,
            "baseline_stage2": {
                "count": len(baseline_props),
                "propositions": [
                    {
                        "content": p.content,
                        "type": p.type,
                        "certainty": p.certainty,
                        "concepts": p.concepts
                    }
                    for p in baseline_props
                ]
            },
            "dspy_stage2": {
                "count": len(dspy_props),
                "propositions": [
                    {
                        "content": p.content,
                        "type": p.type,
                        "certainty": p.certainty,
                        "concepts": p.concepts
                    }
                    for p in dspy_props
                ]
            }
        }

        results["messages"].append(message_result)

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Stage 2 comparison complete! Saved to {output_file}")

    # Summary
    baseline_total = sum(m['baseline_stage2']['count'] for m in results['messages'])
    dspy_total = sum(m['dspy_stage2']['count'] for m in results['messages'])

    print(f"\n📊 SUMMARY")
    print(f"   Baseline Stage 2: {baseline_total} propositions ({baseline_total/len(results['messages']):.1f} avg)")
    print(f"   DSPy Stage 2:     {dspy_total} propositions ({dspy_total/len(results['messages']):.1f} avg)")
    print(f"   Difference:       {baseline_total - dspy_total:+d} ({(baseline_total-dspy_total)/dspy_total*100:+.1f}%)")


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY in .env file")
        exit(1)

    run_stage2_comparison(
        fixed_results_file="/opt/resemantic/FIXED_two_stage_results.json",
        api_key=api_key,
        output_file="/opt/resemantic/stage2_comparison.json"
    )
