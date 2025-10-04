"""
Semantic extraction using FIXED two-stage pipeline (Anthropic API for speed).
"""

import json
import os
from anthropic import Anthropic
from typing import List, Dict


class SemanticExtractor:
    """FIXED two-stage semantic extraction with Anthropic."""

    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-haiku-20241022"

    def extract(
        self,
        message_content: str,
        conversation_context: str,
        role: str,
        timestamp: str,
        message_id: str
    ) -> dict:
        """
        Extract semantic unit and propositions from message.

        Returns:
            {
                'semantic_unit': {...},
                'propositions': [...]
            }
        """

        try:
            import time

            # Stage 1: Extract semantic unit
            start = time.time()
            with open('/tmp/extraction_timing.log', 'a') as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Starting Stage 1 for {role}...\n")

            semantic_unit = self._extract_semantic_unit(
                message_content,
                conversation_context,
                role,
                timestamp,
                message_id
            )
            stage1_time = time.time() - start
            with open('/tmp/extraction_timing.log', 'a') as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Stage 1 completed in {stage1_time:.2f}s\n")

            # Stage 2: Propositionalize
            start = time.time()
            with open('/tmp/extraction_timing.log', 'a') as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Starting Stage 2...\n")

            propositions = self._propositionalize(semantic_unit)
            stage2_time = time.time() - start
            with open('/tmp/extraction_timing.log', 'a') as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Stage 2 completed in {stage2_time:.2f}s\n")

            with open('/tmp/extraction_timing.log', 'a') as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Total extraction time: {stage1_time + stage2_time:.2f}s\n\n")

            return {
                'semantic_unit': semantic_unit,
                'propositions': propositions
            }

        except Exception as e:
            print(f"[EXTRACT] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_semantic_unit(
        self,
        message_content: str,
        conversation_context: str,
        role: str,
        timestamp: str,
        message_id: str
    ) -> dict:
        """Stage 1: Extract semantic unit with FIXED prompt."""

        import time

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

EXEMPLU GREȘIT:
Mesaj: "buna. ce inseamna pentru tine o unitate semantica?"
❌ GREȘIT: "content": "O unitate semantică reprezintă..." (RĂSPUNS la întrebare)
✅ CORECT: "content": "User salută și întreabă ce înseamnă o unitate semantică" (DESCRIERE)

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație:
{conversation_context}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: {role}
Timestamp: {timestamp}
Message: "{message_content}"

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{message_id}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": ["{message_content}"],
    "speaker": "{role}",
    "timestamp": "{timestamp}",
    "type": "<question/statement/response/command/reflection/etc>",
    "narrative_role": "<core/supportive/peripheral>",
    "concepts": ["concept1", "concept2"],
    "entities": ["entitate1", "entitate2"],
    "decisions": ["decizie1"],
    "certainty": "<high/medium/low>",
    "context_dependencies": ["ref1"],
    "impact": "<major/minor/neutral>",
    "relevance": "<high/medium/low>"
}}

REGULI:
- 'content' = DESCRIERE, nu RĂSPUNS
- Dacă mesaj e primă întrebare → certainty: high, context_dependencies: []
- Dacă mesaj continuă conversație → context_dependencies: [mesaje anterioare]
- type = natura mesajului (question, statement, command, etc)
- narrative_role: core (central), supportive (complementar), peripheral (tangențial)
"""

        # Log API call timing
        api_start = time.time()
        with open('/tmp/extraction_timing.log', 'a') as f:
            f.write(f"  -> API call starting (prompt length: {len(prompt)} chars)...\n")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        api_time = time.time() - api_start
        with open('/tmp/extraction_timing.log', 'a') as f:
            f.write(f"  -> API call completed in {api_time:.2f}s\n")

        result_text = response.content[0].text.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        return json.loads(result_text.strip())

    def _propositionalize(self, semantic_unit: dict) -> List[dict]:
        """Stage 2: Break semantic unit into atomic propositions."""

        prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(semantic_unit, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE:
═══════════════════════════════════════════════════════════════════

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitatea semantică
❌ NU defini conceptele menționate
❌ NU explica ce înseamnă termenii
❌ NU genera cunoștințe generale

✅ Doar DESCOMPUNE ce există în unitate
✅ O propoziție = O afirmație verificabilă
✅ Auto-suficiente (cu pronume rezolvate)

EXEMPLE:

Input: "User salută și întreabă ce înseamnă o unitate semantică"
✅ CORECT:
- "User salută"
- "User întreabă ce înseamnă o unitate semantică"

❌ GREȘIT:
- "User salută"
- "User întreabă ce înseamnă o unitate semantică"
- "O unitate semantică este un bloc de sens..." ← HALLUCINATION!

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON array (fără ```json):

[
    {{
        "content": "<propoziție auto-suficientă>",
        "type": "<fact/opinion/question/command>",
        "certainty": "<high/medium/low>",
        "concepts": ["concept1", "concept2"]
    }}
]

CRITERII CALITATE:
- Minim 1, maxim 10 propoziții
- Fiecare înțeleasă fără context
- Acoperire 100% din unitate
- Zero overlap între propoziții
- ZERO informație nouă
"""

        import time

        # Log API call timing
        api_start = time.time()
        with open('/tmp/extraction_timing.log', 'a') as f:
            f.write(f"  -> API call starting (prompt length: {len(prompt)} chars)...\n")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        api_time = time.time() - api_start
        with open('/tmp/extraction_timing.log', 'a') as f:
            f.write(f"  -> API call completed in {api_time:.2f}s\n")

        result_text = response.content[0].text.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        return json.loads(result_text.strip())
