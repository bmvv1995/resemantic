"""
Stage 2 comparison with FIXED Baseline prompt.

FIX: Strict prohibition against adding new information or definitions.
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


class FixedBaselineStage2:
    """Baseline with STRICT no-hallucination prompt."""

    def __init__(self, lm):
        self.lm = lm

    def propositionalize(self, semantic_unit: Dict) -> List[Proposition]:
        """Break semantic unit into propositions - STRICT version."""

        prompt = f"""Descompune această unitate semantică în propoziții atomice pentru embeddings.

═══════════════════════════════════════════════════════════════════
UNITATEA SEMANTICĂ DE DESCOMPUS:
═══════════════════════════════════════════════════════════════════

{semantic_unit['content']}

Concepte menționate: {', '.join(semantic_unit['concepts'])}
Type: {semantic_unit['type']}
Narrative role: {semantic_unit['narrative_role']}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE - CITEȘTE CU ATENȚIE:
═══════════════════════════════════════════════════════════════════

ATOMICITATE:
✅ Fiecare propoziție = UN singur fapt/opinie/afirmație atomică
✅ Fiecare propoziție trebuie să fie auto-suficientă
✅ Split compound statements în multiple propositions

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitatea semantică
❌ NU defini conceptele menționate
❌ NU explica ce înseamnă termenii
❌ NU genera cunoștințe generale
❌ NU repeta aceeași informație

CE FACI:
✅ Doar DESCRII ce spune unitatea semantică
✅ Păstrezi nuanțe (certitudine, opinie vs fapt)
✅ Split bazat pe narrative role:
   - "supportive"/"peripheral": maxim 2-3 propositions
   - "core": toate propozițiile atomice NECESARE (din semantic unit!)

EXEMPLE:

Semantic unit: "User-ul întreabă dacă asistentul cunoaște despre propoziționalizare"
✅ CORECT:
  - "User-ul întreabă despre propoziționalizare"
❌ GREȘIT:
  - "User-ul întreabă despre propoziționalizare"
  - "Propoziționalizarea este procesul de..." (hallucination - nu e în semantic unit!)

Semantic unit: "Asistentul explică că X este Y și oferă exemple: A, B, C"
✅ CORECT:
  - "Asistentul explică că X este Y"
  - "Asistentul oferă exemplul A"
  - "Asistentul oferă exemplul B"
  - "Asistentul oferă exemplul C"
❌ GREȘIT:
  - "X este Y" (pierde că asistentul o spune)
  - "X este important" (hallucination)

═══════════════════════════════════════════════════════════════════
RETURNEAZĂ JSON:
═══════════════════════════════════════════════════════════════════

[
  {{
    "content": "propoziție atomică DOAR din semantic unit",
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
            print(f"Fixed Baseline Stage 2 error: {e}")
            print(f"Response: {response_text[:200]}")
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
    """DSPy propositionalization (unchanged)."""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(PropositionSignature)

    def propositionalize(self, semantic_unit: Dict) -> List[Proposition]:
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
        - Must be self-contained
        - NO new information not in semantic unit
        - NO repetition
        - For supportive/peripheral: max 2-3 propositions
        - For core: all necessary atomic propositions
        """
    )


def run_fixed_stage2_comparison(fixed_results_file: str, api_key: str, output_file: str):
    """Compare FIXED Baseline vs DSPy for Stage 2."""

    print("🔧 Setting up FIXED Stage 2 comparison...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    fixed_baseline_stage2 = FixedBaselineStage2(lm)
    dspy_stage2 = DSPyStage2()

    # Load Stage 1 results
    with open(fixed_results_file, 'r', encoding='utf-8') as f:
        fixed_data = json.load(f)

    print(f"📖 Processing {len(fixed_data['messages'])} semantic units...\n")

    results = {
        "metadata": {
            "test": "Stage 2 comparison - FIXED Baseline vs DSPy",
            "stage_1": "FIXED semantic units (same for both)",
            "stage_2a": "FIXED Baseline (strict no-hallucination)",
            "stage_2b": "DSPy structured signatures",
            "total_messages": len(fixed_data['messages'])
        },
        "messages": []
    }

    for msg in fixed_data['messages']:
        msg_num = msg['message_index']
        su = msg['semantic_unit']

        print(f"{'='*70}")
        print(f"MESSAGE {msg_num} - {su['speaker'].upper()}")
        print(f"{'='*70}")
        print(f"Semantic Unit: {su['content'][:80]}...")

        # FIXED Baseline Stage 2
        print("\n🔵 FIXED Baseline Stage 2...")
        fixed_baseline_props = fixed_baseline_stage2.propositionalize(su)
        print(f"   → {len(fixed_baseline_props)} propositions")

        # DSPy Stage 2
        print("🟣 DSPy Stage 2...")
        dspy_props = dspy_stage2.propositionalize(su)
        print(f"   → {len(dspy_props)} propositions")
        print()

        message_result = {
            "message_index": msg_num,
            "original_content": msg['original_content'],
            "semantic_unit": su,
            "fixed_baseline_stage2": {
                "count": len(fixed_baseline_props),
                "propositions": [
                    {
                        "content": p.content,
                        "type": p.type,
                        "certainty": p.certainty,
                        "concepts": p.concepts
                    }
                    for p in fixed_baseline_props
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

    print(f"✅ FIXED Stage 2 comparison complete! Saved to {output_file}")

    # Summary
    fixed_baseline_total = sum(m['fixed_baseline_stage2']['count'] for m in results['messages'])
    dspy_total = sum(m['dspy_stage2']['count'] for m in results['messages'])

    print(f"\n📊 SUMMARY")
    print(f"   FIXED Baseline: {fixed_baseline_total} propositions ({fixed_baseline_total/len(results['messages']):.1f} avg)")
    print(f"   DSPy:           {dspy_total} propositions ({dspy_total/len(results['messages']):.1f} avg)")

    if fixed_baseline_total != dspy_total:
        diff_pct = abs((fixed_baseline_total - dspy_total) / max(fixed_baseline_total, dspy_total) * 100)
        print(f"   Difference:     {fixed_baseline_total - dspy_total:+d} ({diff_pct:.1f}%)")
    else:
        print(f"   Difference:     0 (EQUAL!)")


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY in .env file")
        exit(1)

    run_fixed_stage2_comparison(
        fixed_results_file="/opt/resemantic/FIXED_two_stage_results.json",
        api_key=api_key,
        output_file="/opt/resemantic/stage2_fixed_comparison.json"
    )
