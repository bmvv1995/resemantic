"""
Two-stage pipeline with FIXED Stage 1 prompt.

FIX: Separate system role (analyzer) from conversation data to prevent LLM confusion.
"""

import json
import dspy
from typing import List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import os


@dataclass
class EnhancedSemanticUnit:
    """Rich semantic unit with full metadata."""
    unit_id: str
    content: str
    original_fragments: List[str]
    speaker: str
    timestamp: str
    type: str
    narrative_role: str
    concepts: List[str]
    entities: List[str]
    decisions: List[str]
    certainty: str
    context_dependencies: List[str]
    impact: str
    relevance: str


@dataclass
class Proposition:
    """Atomic proposition for embeddings."""
    content: str
    type: str
    certainty: str
    concepts: List[str]


class FixedTwoStagePipeline:
    """Two-stage pipeline with clear system/data separation."""

    def __init__(self, lm):
        self.lm = lm

    # ========================================================================
    # STAGE 1: Semantic Unit Extraction (FIXED PROMPT)
    # ========================================================================

    def extract_semantic_unit(
        self,
        message_content: str,
        conversation_context: str,
        role: str,
        timestamp: str,
        message_id: int
    ) -> EnhancedSemanticUnit:
        """Extract semantic unit with CLEAR role separation."""

        # Determine if first message
        is_first_message = (conversation_context == "Start of conversation")

        prompt = f"""TU EȘTI UN ANALIZOR DE CONVERSAȚII. NU PARTICIPI LA CONVERSAȚIE - DOAR O ANALIZEZI.

═══════════════════════════════════════════════════════════════════
TASK-UL TĂU:
═══════════════════════════════════════════════════════════════════

Primești mesaje dintr-o conversație dintre USER și ASSISTANT.
Transformi fiecare mesaj într-o unitate semantică cu metadata completă.

IMPORTANT - CITEȘTE CU ATENȚIE:
❌ Mesajele NU sunt adresate ție
❌ NU răspunde la întrebări din conversație
❌ NU genera conținut care nu e în mesaj
✅ Doar DESCRII ce spune vorbitorul
✅ Reformulezi pentru claritate gramaticală
✅ Rezolvi referințe și expandezi cu context

═══════════════════════════════════════════════════════════════════
CONVERSAȚIA DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Mesaj #{message_id} - Speaker: {role.upper()}
Timestamp: {timestamp}

{"[Acesta e primul mesaj - nu are context anterior]" if is_first_message else f"Context anterior:\\n{conversation_context}"}

Mesajul de analizat:
\"\"\"
{message_content}
\"\"\"

═══════════════════════════════════════════════════════════════════
REGULI DE ANALIZĂ:
═══════════════════════════════════════════════════════════════════

REFORMULARE:
- Dacă e primul mesaj (fără context): reformulează pentru sens gramatical complet
- Dacă are context: rezolvă referințe (ea→nume, asta→concept, da→confirmă ce?)
- Expandează răspunsuri scurte ("da", "ok") cu contextul implicit
- Fă deciziile ascunse explicite

PENTRU USER MESSAGES:
- Descrie CE cere/spune user-ul
- Identifică tipul: request/question/agreement/decision/feedback
- Extrage conceptele menționate

PENTRU ASSISTANT MESSAGES:
- Descrie CE explică/răspunde assistant-ul
- Technical explanations → narrative_role: "core" dacă adaugă knowledge esențial
- Encouragement/confirmations → narrative_role: "supportive"
- Implementation details → narrative_role: "core" dacă actionable
- Meta-commentary → narrative_role: "peripheral"

CLASIFICARE NARRATIVE_ROLE:
- "core": Contribuie direct la construcția ideilor și deciziilor
- "supportive": Susține conversația dar nu e esențial pentru înțelegere
- "peripheral": Context sau zgomot, păstrat pentru completitudine

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON):
═══════════════════════════════════════════════════════════════════

{{
  "content": "Descriere completă a ce SPUNE vorbitorul în acest mesaj (NU răspunsul la o întrebare din conversație!)",
  "type": "request|decision|information|uncertainty|confirmation|technical_explanation|encouragement|implementation_detail|agreement|question",
  "narrative_role": "core|supportive|peripheral",
  "concepts": ["concepte menționate sau discutate"],
  "entities": ["nume, persoane, organizații menționate"],
  "decisions": ["decizii explicite sau implicite"],
  "certainty": "high|medium|low",
  "context_dependencies": ["la ce se referă din mesajele anterioare"],
  "impact": "major|minor|neutral",
  "relevance": "high|medium|low"
}}

EXEMPLU:
Dacă user spune: "buna. ce inseamna pentru tine o unitate semantica?"
✅ CORECT: "User-ul salută și întreabă ce înseamnă o unitate semantică pentru asistent"
❌ GREȘIT: "Bună! O unitate semantică este..." (asta ar fi răspuns la întrebare, nu descriere!)
"""

        response = self.lm(prompt)
        response_text = self._extract_text(response)
        response_text = self._strip_markdown(response_text)

        try:
            data = json.loads(response_text)
            return EnhancedSemanticUnit(
                unit_id=f"unit_{message_id:03d}",
                content=data.get('content', message_content),
                original_fragments=[message_content],
                speaker=role,
                timestamp=timestamp,
                type=data.get('type', 'information'),
                narrative_role=data.get('narrative_role', 'core'),
                concepts=data.get('concepts', []),
                entities=data.get('entities', []),
                decisions=data.get('decisions', []),
                certainty=data.get('certainty', 'medium'),
                context_dependencies=data.get('context_dependencies', []),
                impact=data.get('impact', 'neutral'),
                relevance=data.get('relevance', 'medium')
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Stage 1 parsing error: {e}")
            print(f"Response: {response_text[:200]}")
            return EnhancedSemanticUnit(
                unit_id=f"unit_{message_id:03d}",
                content=message_content,
                original_fragments=[message_content],
                speaker=role,
                timestamp=timestamp,
                type='information',
                narrative_role='core',
                concepts=[],
                entities=[],
                decisions=[],
                certainty='medium',
                context_dependencies=[],
                impact='neutral',
                relevance='medium'
            )

    # ========================================================================
    # STAGE 2: Propositionalization (unchanged)
    # ========================================================================

    def propositionalize(self, semantic_unit: EnhancedSemanticUnit) -> List[Proposition]:
        """Break semantic unit into atomic propositions."""

        prompt = f"""Descompune această unitate semantică în propoziții atomice pentru embeddings.

Unitate semantică:
{semantic_unit.content}

Concepte principale: {', '.join(semantic_unit.concepts)}
Type: {semantic_unit.type}
Narrative role: {semantic_unit.narrative_role}

Reguli:
- Fiecare propoziție = UN fapt/opinie/afirmație atomică
- Fiecare propoziție trebuie să fie auto-suficientă
- NU adăuga informație nouă care nu e în unitatea semantică
- NU repeta aceeași informație
- Păstrează nuanțe (certitudine, opinie vs fapt)
- Pentru "supportive" sau "peripheral": maxim 2-3 propositions
- Pentru "core": toate propozițiile atomice necesare

Returnează JSON:
[
  {{
    "content": "propoziție atomică auto-suficientă",
    "type": "fact|opinion|question|agreement|decision",
    "certainty": "high|medium|low",
    "concepts": ["concepte", "cheie"]
  }}
]
"""

        response = self.lm(prompt)
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
            print(f"Stage 2 parsing error: {e}")
            return []

    # ========================================================================
    # Pipeline
    # ========================================================================

    def process_message(
        self,
        message_content: str,
        conversation_context: str,
        role: str,
        timestamp: str,
        message_id: int
    ) -> Dict:
        """Execute full pipeline."""

        semantic_unit = self.extract_semantic_unit(
            message_content,
            conversation_context,
            role,
            timestamp,
            message_id
        )

        propositions = self.propositionalize(semantic_unit)

        return {
            "semantic_unit": {
                "unit_id": semantic_unit.unit_id,
                "content": semantic_unit.content,
                "speaker": semantic_unit.speaker,
                "timestamp": semantic_unit.timestamp,
                "type": semantic_unit.type,
                "narrative_role": semantic_unit.narrative_role,
                "concepts": semantic_unit.concepts,
                "entities": semantic_unit.entities,
                "decisions": semantic_unit.decisions,
                "certainty": semantic_unit.certainty,
                "context_dependencies": semantic_unit.context_dependencies,
                "impact": semantic_unit.impact,
                "relevance": semantic_unit.relevance
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


def run_fixed_analysis(conversation_file: str, api_key: str, output_file: str):
    """Run FIXED two-stage pipeline."""

    print("🔧 Setting up FIXED two-stage pipeline...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    pipeline = FixedTwoStagePipeline(lm)

    with open(conversation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    messages = data['conversation']

    print(f"📖 Processing {len(messages)} messages with FIXED pipeline...\n")

    results = {
        "metadata": {
            "pipeline": "fixed two-stage",
            "fix": "clear system/data separation to prevent LLM confusion",
            "stage_1": "describe what speaker says (NOT answer questions)",
            "stage_2": "atomic propositionalization",
            "total_messages": len(messages)
        },
        "messages": []
    }

    for idx, msg in enumerate(messages):
        print(f"{'='*70}")
        print(f"MESSAGE {idx + 1}/{len(messages)} - {msg['role'].upper()}")
        print(f"{'='*70}")
        print(f"Original: {msg['content'][:80]}...")

        context = build_context(messages, idx, window=3)

        result = pipeline.process_message(
            message_content=msg['content'],
            conversation_context=context,
            role=msg['role'],
            timestamp=msg['timestamp'],
            message_id=idx + 1
        )

        print(f"\n📝 Semantic Unit:")
        print(f"   Type: {result['semantic_unit']['type']}")
        print(f"   Role: {result['semantic_unit']['narrative_role']}")
        print(f"   Content: {result['semantic_unit']['content'][:100]}...")

        if result['semantic_unit']['concepts']:
            print(f"   Concepts: {', '.join(result['semantic_unit']['concepts'][:3])}")

        print(f"\n⚛️  Propositions: {len(result['propositions'])}")
        for i, prop in enumerate(result['propositions'][:2], 1):
            print(f"   {i}. [{prop['type']}] {prop['content'][:60]}...")
        if len(result['propositions']) > 2:
            print(f"   ... and {len(result['propositions']) - 2} more")
        print()

        message_result = {
            "message_index": idx + 1,
            "original_content": msg['content'],
            "context_used": context,
            "semantic_unit": result['semantic_unit'],
            "propositions": result['propositions'],
            "proposition_count": len(result['propositions'])
        }

        results["messages"].append(message_result)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ FIXED analysis complete! Saved to {output_file}")

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

    run_fixed_analysis(
        conversation_file="/opt/resemantic/test_conversation.json",
        api_key=api_key,
        output_file="/opt/resemantic/FIXED_two_stage_results.json"
    )
