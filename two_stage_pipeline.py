"""
Two-stage pipeline:
1. Semantic Unit Extraction (with context) - summarizes message meaning
2. Propositionalization (without context) - atomizes semantic units

This separates concerns: understanding vs granularization
"""

import json
import dspy
from typing import List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import os


@dataclass
class SemanticUnit:
    """High-level semantic summary of a message."""
    content: str
    narrative_role: str
    main_concepts: List[str]


@dataclass
class Proposition:
    """Atomic, self-contained factual statement."""
    content: str
    type: str
    certainty: str
    concepts: List[str]


class TwoStagePipeline:
    """Process messages in two stages: understand, then atomize."""

    def __init__(self, lm):
        self.lm = lm

    # ========================================================================
    # STAGE 1: Semantic Unit Extraction (WITH context)
    # ========================================================================

    def extract_semantic_unit(
        self,
        message_content: str,
        conversation_context: str,
        role: str
    ) -> SemanticUnit:
        """Extract semantic unit with full context understanding."""

        prompt = f"""Analizează acest mesaj și creează o unitate semantică coerentă.

Context conversație:
{conversation_context}

Mesaj curent ({role}):
{message_content}

Reguli:
- Rezolvă toate referințele (ea → nume, asta → concept specific, da → la ce se referă)
- Expandează răspunsuri scurte cu contextul implicit
- Capturează DESPRE CE vorbește mesajul (topic principal)
- Pentru acord/entuziasm, specifică la CE se referă
- Păstrează nuanțe (entuziasm, incertitudine, etc)

Returnează JSON:
{{
  "semantic_unit": "Descriere coerentă și completă a mesajului",
  "narrative_role": "core|supportive|peripheral",
  "main_concepts": ["concept1", "concept2"]
}}
"""

        response = self.lm(prompt)

        # Parse response
        response_text = self._extract_text(response)
        response_text = self._strip_markdown(response_text)

        try:
            data = json.loads(response_text)
            return SemanticUnit(
                content=data['semantic_unit'],
                narrative_role=data.get('narrative_role', 'core'),
                main_concepts=data.get('main_concepts', [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Stage 1 error: {e}")
            return SemanticUnit(
                content=message_content,
                narrative_role='core',
                main_concepts=[]
            )

    # ========================================================================
    # STAGE 2: Propositionalization (WITHOUT context)
    # ========================================================================

    def propositionalize(self, semantic_unit: SemanticUnit) -> List[Proposition]:
        """Break semantic unit into atomic propositions WITHOUT additional context."""

        prompt = f"""Descompune această unitate semantică în propoziții atomice.

Unitate semantică:
{semantic_unit.content}

Concepte principale: {', '.join(semantic_unit.main_concepts)}

Reguli:
- Fiecare propoziție = UN fapt/opinie/afirmație atomică
- Fiecare propoziție trebuie să fie auto-suficientă
- NU adăuga informație nouă
- NU repeta aceeași informație
- Păstrează nuanțe (certitudine, opinie vs fapt)

Returnează JSON:
[
  {{
    "content": "propoziție atomică",
    "type": "fact|opinion|question|agreement|decision",
    "certainty": "high|medium|low",
    "concepts": ["concepte", "cheie"]
  }}
]
"""

        response = self.lm(prompt)

        # Parse response
        response_text = self._extract_text(response)
        response_text = self._strip_markdown(response_text)

        try:
            propositions_data = json.loads(response_text)
            return [
                Proposition(
                    content=p['content'],
                    type=p.get('type', 'fact'),
                    certainty=p.get('certainty', 'medium'),
                    concepts=p.get('concepts', [])
                )
                for p in propositions_data
            ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Stage 2 error: {e}")
            return []

    # ========================================================================
    # Pipeline execution
    # ========================================================================

    def process_message(
        self,
        message_content: str,
        conversation_context: str,
        role: str
    ) -> Dict:
        """Execute full two-stage pipeline."""

        # Stage 1: Understand message in context
        semantic_unit = self.extract_semantic_unit(
            message_content,
            conversation_context,
            role
        )

        # Stage 2: Atomize semantic unit (no context)
        propositions = self.propositionalize(semantic_unit)

        return {
            "semantic_unit": {
                "content": semantic_unit.content,
                "narrative_role": semantic_unit.narrative_role,
                "main_concepts": semantic_unit.main_concepts
            },
            "propositions": [
                {
                    "content": p.content,
                    "type": p.type,
                    "certainty": p.certainty,
                    "concepts": p.concepts
                }
                for p in propositions
            ]
        }

    # ========================================================================
    # Helpers
    # ========================================================================

    def _extract_text(self, response):
        """Extract text from various response formats."""
        if isinstance(response, list) and len(response) > 0:
            return response[0]
        elif isinstance(response, str):
            return response
        elif hasattr(response, 'choices'):
            return response.choices[0].message.content
        else:
            return str(response)

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown code blocks."""
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return text.strip()


def run_two_stage_analysis(conversation_file: str, api_key: str, output_file: str):
    """Run two-stage pipeline on conversation."""

    print("🔧 Setting up two-stage pipeline...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    pipeline = TwoStagePipeline(lm)

    # Load conversation
    with open(conversation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    messages = data['conversation']

    print(f"📖 Processing {len(messages)} messages with two-stage pipeline...\n")

    results = {
        "metadata": {
            "pipeline": "two-stage (semantic unit → propositions)",
            "stage_1": "extract semantic unit WITH context",
            "stage_2": "propositionalize WITHOUT context",
            "total_messages": len(messages)
        },
        "messages": []
    }

    # Process each message
    for idx, msg in enumerate(messages):
        print(f"{'='*70}")
        print(f"MESSAGE {idx + 1}/{len(messages)} - {msg['role'].upper()}")
        print(f"{'='*70}")
        print(f"Original: {msg['content'][:80]}...")

        # Build context
        context = build_context(messages, idx, window=3)

        # Process
        result = pipeline.process_message(
            message_content=msg['content'],
            conversation_context=context,
            role=msg['role']
        )

        print(f"\n📝 Semantic Unit:")
        print(f"   {result['semantic_unit']['content'][:100]}...")
        print(f"\n⚛️  Propositions: {len(result['propositions'])}")
        for i, prop in enumerate(result['propositions'][:3], 1):
            print(f"   {i}. [{prop['type']}] {prop['content'][:60]}...")
        if len(result['propositions']) > 3:
            print(f"   ... and {len(result['propositions']) - 3} more")
        print()

        # Store
        message_result = {
            "message_index": idx + 1,
            "role": msg['role'],
            "original_content": msg['content'],
            "context_used": context,
            "semantic_unit": result['semantic_unit'],
            "propositions": result['propositions'],
            "proposition_count": len(result['propositions'])
        }

        results["messages"].append(message_result)

    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Two-stage analysis complete! Saved to {output_file}")

    # Summary
    total_props = sum(m['proposition_count'] for m in results['messages'])
    print(f"\n📊 SUMMARY")
    print(f"   Total propositions: {total_props}")
    print(f"   Avg per message: {total_props / len(messages):.1f}")


def build_context(messages: List[Dict], current_idx: int, window: int = 3) -> str:
    """Build conversation context."""
    if current_idx == 0:
        return "Start of conversation"

    start = max(0, current_idx - window)
    context_msgs = messages[start:current_idx]

    return "\n".join([
        f"{msg['role']}: {msg['content'][:200]}..."
        for msg in context_msgs
    ])


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY in .env file")
        exit(1)

    run_two_stage_analysis(
        conversation_file="/opt/resemantic/test_conversation.json",
        api_key=api_key,
        output_file="/opt/resemantic/two_stage_results.json"
    )
