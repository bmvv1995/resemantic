"""
ReSemantic Batch Extraction Pipeline - LangGraph Definition
Processes user + assistant messages together with shared context
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# State definition for batch processing
class BatchExtractionState(TypedDict):
    """State for batch extraction of conversation pair."""
    # Input
    user_message: str
    assistant_message: str
    conversation_context: str  # Last 4-5 messages formatted
    timestamp: str
    user_message_id: str
    assistant_message_id: str

    # Stage 1 outputs
    user_semantic_unit: Dict
    assistant_semantic_unit: Dict

    # Stage 2 outputs
    user_propositions: List[Dict]
    assistant_propositions: List[Dict]

    # Metadata
    stage1_user_time: float
    stage1_assistant_time: float
    stage2_user_time: float
    stage2_assistant_time: float
    error: str


# Initialize LLM
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.3,
    max_tokens=1500,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def extract_user_semantic_unit(state: BatchExtractionState) -> Dict:
    """Stage 1a: Extract semantic unit for USER message."""

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

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (ultimele mesaje):
{state['conversation_context']}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: user
Timestamp: {state['timestamp']}
Message: "{state['user_message']}"

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{state['user_message_id']}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": ["{state['user_message']}"],
    "speaker": "user",
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
            "user_semantic_unit": semantic_unit,
            "stage1_user_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 1 User error: {str(e)}",
            "user_semantic_unit": {},
            "stage1_user_time": time.time() - start
        }


def extract_assistant_semantic_unit(state: BatchExtractionState) -> Dict:
    """Stage 1b: Extract semantic unit for ASSISTANT message."""

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

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (ultimele mesaje):
{state['conversation_context']}

User message tocmai procesat: {state['user_message']}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: assistant
Timestamp: {state['timestamp']}
Message: "{state['assistant_message']}"

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{state['assistant_message_id']}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": ["{state['assistant_message']}"],
    "speaker": "assistant",
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
- 'content' = DESCRIERE a răspunsului assistant-ului
- type = natura răspunsului (response, explanation, question, etc)
- narrative_role: core (conținut esențial), supportive (suport), peripheral (context)
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
            "assistant_semantic_unit": semantic_unit,
            "stage1_assistant_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 1 Assistant error: {str(e)}",
            "assistant_semantic_unit": {},
            "stage1_assistant_time": time.time() - start
        }


def propositionalize_user(state: BatchExtractionState) -> Dict:
    """Stage 2a: Break USER semantic unit into atomic propositions."""

    import time
    start = time.time()

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(state['user_semantic_unit'], indent=2, ensure_ascii=False)}

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
            "user_propositions": propositions,
            "stage2_user_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 2 User error: {str(e)}",
            "user_propositions": [],
            "stage2_user_time": time.time() - start
        }


def propositionalize_assistant(state: BatchExtractionState) -> Dict:
    """Stage 2b: Break ASSISTANT semantic unit into atomic propositions."""

    import time
    start = time.time()

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(state['assistant_semantic_unit'], indent=2, ensure_ascii=False)}

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
            "assistant_propositions": propositions,
            "stage2_assistant_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 2 Assistant error: {str(e)}",
            "assistant_propositions": [],
            "stage2_assistant_time": time.time() - start
        }


# Build graph
workflow = StateGraph(BatchExtractionState)

# Add nodes
workflow.add_node("extract_user_su", extract_user_semantic_unit)
workflow.add_node("extract_assistant_su", extract_assistant_semantic_unit)
workflow.add_node("propositionalize_user", propositionalize_user)
workflow.add_node("propositionalize_assistant", propositionalize_assistant)

# Add edges - linear flow
workflow.set_entry_point("extract_user_su")
workflow.add_edge("extract_user_su", "extract_assistant_su")
workflow.add_edge("extract_assistant_su", "propositionalize_user")
workflow.add_edge("propositionalize_user", "propositionalize_assistant")
workflow.add_edge("propositionalize_assistant", END)

# Compile
graph = workflow.compile()
