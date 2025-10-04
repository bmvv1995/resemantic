"""
ReSemantic Two-Stage Extraction Pipeline - LangGraph Definition
"""

from typing import TypedDict, List, Dict, Annotated
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# State definition
class ExtractionState(TypedDict):
    """State for the extraction pipeline."""
    # Input
    message_content: str
    conversation_context: str
    role: str
    timestamp: str
    message_id: str

    # Stage 1 output
    semantic_unit: Dict

    # Stage 2 output
    propositions: List[Dict]

    # Metadata
    stage1_time: float
    stage2_time: float
    error: str


# Initialize LLM
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.3,
    max_tokens=1500,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def stage1_extract_semantic_unit(state: ExtractionState) -> ExtractionState:
    """Stage 1: Extract semantic unit with metadata."""

    import time
    start = time.time()

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
{state['conversation_context']}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: {state['role']}
Timestamp: {state['timestamp']}
Message: "{state['message_content']}"

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{state['message_id']}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": ["{state['message_content']}"],
    "speaker": "{state['role']}",
    "timestamp": "{state['timestamp']}",
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

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        semantic_unit = json.loads(result_text.strip())

        return {
            "semantic_unit": semantic_unit,
            "stage1_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 1 error: {str(e)}",
            "semantic_unit": {},
            "stage1_time": time.time() - start
        }


def stage2_propositionalize(state: ExtractionState) -> ExtractionState:
    """Stage 2: Break semantic unit into atomic propositions."""

    import time
    start = time.time()

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(state['semantic_unit'], indent=2, ensure_ascii=False)}

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

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        propositions = json.loads(result_text.strip())

        return {
            "propositions": propositions,
            "stage2_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 2 error: {str(e)}",
            "propositions": [],
            "stage2_time": time.time() - start
        }


# Build graph
workflow = StateGraph(ExtractionState)

# Add nodes
workflow.add_node("stage1_semantic_unit", stage1_extract_semantic_unit)
workflow.add_node("stage2_propositionalize", stage2_propositionalize)

# Add edges
workflow.set_entry_point("stage1_semantic_unit")
workflow.add_edge("stage1_semantic_unit", "stage2_propositionalize")
workflow.add_edge("stage2_propositionalize", END)

# Compile
graph = workflow.compile()
