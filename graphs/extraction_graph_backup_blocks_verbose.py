"""
ReSemantic Batch Extraction Pipeline - LangGraph Definition
WITH METADATA BLOCKS (resource, decision, document)
Processes user + assistant messages together with shared context
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Neo4jClient, ArchiveDB, EmbeddingGenerator, cosine_similarity
from config import ExtractionConfig, EmbeddingConfig, Neo4jConfig, SQLiteConfig
from graphs.storage_nodes import generate_embeddings, store_propositions, create_edges

# Load environment variables
load_dotenv()


# State definition for batch processing
class BatchExtractionState(TypedDict):
    """State for batch extraction of conversation pair."""
    # Input
    user_message: str
    assistant_message: str
    assistant_reasoning: str  # NEW: Reasoning/thinking from assistant response
    conversation_history: List[Dict]  # Full conversation history before current pair
    timestamp: str
    user_message_id: str
    assistant_message_id: str

    # Stage 1 outputs
    user_semantic_unit: Dict
    assistant_semantic_unit: Dict

    # Stage 2 outputs
    user_propositions: List[Dict]
    assistant_propositions: List[Dict]

    # Embeddings
    all_propositions: List[Dict]  # Combined propositions with metadata
    proposition_embeddings: List[List[float]]  # Generated embeddings

    # Metadata
    stage1_user_time: float
    stage1_assistant_time: float
    stage2_user_time: float
    stage2_assistant_time: float
    embedding_time: float
    storage_time: float
    edge_creation_time: float
    error: str

    # Storage outputs
    stored_proposition_ids: List[str]


# Initialize LLM with config
llm = ChatAnthropic(
    model=ExtractionConfig.LLM_MODEL,
    temperature=ExtractionConfig.LLM_TEMPERATURE,
    max_tokens=ExtractionConfig.LLM_MAX_TOKENS,
    api_key=ExtractionConfig.ANTHROPIC_API_KEY
)


def build_context_from_history(history: List[Dict], max_messages: int = None) -> str:
    """Build context string from conversation history."""
    if max_messages is None:
        max_messages = ExtractionConfig.CONTEXT_MAX_MESSAGES

    if not history:
        return "Start of conversation"

    recent = history[-max_messages:] if len(history) > max_messages else history
    context_lines = []

    for msg in recent:
        role = "User" if msg['role'] == 'user' else "Assistant"
        context_lines.append(f"{role}: {msg['content']}")

    return "\n".join(context_lines)


def extract_user_semantic_unit(state: BatchExtractionState) -> Dict:
    """Stage 1a: Extract semantic unit + metadata blocks for USER message."""

    import time
    import json as json_lib
    start = time.time()

    # Build context from history
    context = build_context_from_history(state.get('conversation_history', []))

    prompt = f"""TU EȘTI UN ANALIZOR DE CONVERSAȚII. NU PARTICIPI LA CONVERSAȚIE - DOAR O ANALIZEZI.

═══════════════════════════════════════════════════════════════════
TASK-UL TĂU:
═══════════════════════════════════════════════════════════════════

Primești mesaje dintr-o conversație dintre USER și ASSISTANT.
Transformi fiecare mesaj într-o unitate semantică cu metadata completă + BLOCKS.

IMPORTANT - CITEȘTE CU ATENȚIE:
❌ Mesajele NU sunt adresate ție
❌ NU răspunde la întrebări din conversație  
❌ NU genera conținut care nu e în mesaj
✅ Doar DESCRII ce spune vorbitorul
✅ Reformulezi pentru claritate gramaticală
✅ Rezolvi referințe (exemplu: "da" → "User confirmă X din context")

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (ultimele mesaje):
{context}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: user
Timestamp: {state['timestamp']}
Message: {json_lib.dumps(state['user_message'], ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (DOAR JSON, fără ```):
═══════════════════════════════════════════════════════════════════

{{
    "unit_id": "{state['user_message_id']}",
    "content": "<reformulare clară și completă cu context rezolvat>",
    "speaker": "user",
    "timestamp": "{state['timestamp']}",
    
    "type": "<decision|resource|document|question|statement|confirmation|etc>",
    "certainty": "<high|medium|low>",
    "narrative_role": "<core|supportive|peripheral>",
    
    "concepts": ["concept_specific_1", "concept_2"],
    
    "block_metadata": {{
        "resource_url": "<URL exact dacă există în mesaj>",
        "resource_type": "<documentation|api|guide|tool - dacă există URL>",
        "resource_title": "<titlu din context - dacă aplicabil>",
        "discussed_context": "<pentru ce e relevant URL-ul>",
        
        "decision_choice": "<ce s-a decis - dacă type=decision>",
        "decision_reason": "<DE CE (reasoning) - OBLIGATORIU pentru decizii>",
        "decision_alternatives": ["<ce s-a respins>"],
        "decision_confidence": "<high|medium|low>",
        
        "doc_filename": "<nume fișier - dacă există path>",
        "doc_location": "<path complet - dacă există>",
        "doc_purpose": "<pentru ce e folosit>",
        "doc_key_settings": ["<setări relevante dacă e config>"]
    }}
}}

═══════════════════════════════════════════════════════════════════
REGULI BLOCKS:
═══════════════════════════════════════════════════════════════════

1. RESOURCE BLOCK (type="resource"):
   Când: mesaj conține URL, link, documentație
   Extrage: resource_url (obligatoriu), resource_type, resource_title, discussed_context
   
2. DECISION BLOCK (type="decision"):  
   Când: mesaj conține decizie (alegem, decidem, optăm)
   Extrage: decision_choice, decision_reason (WHY OBLIGATORIU!), decision_alternatives, decision_confidence
   
3. DOCUMENT BLOCK (type="document"):
   Când: mesaj conține file path, config reference
   Extrage: doc_filename, doc_location, doc_purpose, doc_key_settings

DEPTH TIERS:
- Greeting/confirmation → minimal (type + temporal)
- Technical/question → detailed
- Decision → MAXIMAL (include WHY obligatoriu!)

CONCEPTS:
- Specifice: "webhook_retry", "exponential_backoff", "API_authentication"
- NU generice: "comunicare", "interacțiune", "discuție"
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
    """Stage 1b: Extract semantic unit + metadata blocks for ASSISTANT message."""

    import time
    import json as json_lib
    start = time.time()

    # Build context including user message
    context_messages = list(state.get('conversation_history', []))
    context_messages.append({"role": "user", "content": state['user_message']})
    context = build_context_from_history(context_messages)

    # Include reasoning if available
    reasoning_note = ""
    if state.get('assistant_reasoning'):
        reasoning_note = f"\n\nAssistant Reasoning (thinking):\n{state['assistant_reasoning']}"

    prompt = f"""TU EȘTI UN ANALIZOR DE CONVERSAȚII. NU PARTICIPI LA CONVERSAȚIE - DOAR O ANALIZEZI.

═══════════════════════════════════════════════════════════════════
TASK-UL TĂU:
═══════════════════════════════════════════════════════════════════

Primești mesaje dintr-o conversație dintre USER și ASSISTANT.
Transformi fiecare mesaj într-o unitate semantică cu metadata completă + BLOCKS.

IMPORTANT - CITEȘTE CU ATENȚIE:
❌ Mesajele NU sunt adresate ție
❌ NU răspunde la întrebări din conversație
❌ NU genera conținut care nu e în mesaj  
✅ Doar DESCRII ce spune assistant-ul
✅ Reformulezi pentru claritate gramaticală
✅ Capturezi reasoning dacă e disponibil

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (inclusiv user message):
{context}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: assistant
Timestamp: {state['timestamp']}
Message: {json_lib.dumps(state['assistant_message'], ensure_ascii=False)}{reasoning_note}

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (DOAR JSON, fără ```):
═══════════════════════════════════════════════════════════════════

{{
    "unit_id": "{state['assistant_message_id']}",
    "content": "<descriere completă răspuns assistant>",
    "speaker": "assistant",
    "timestamp": "{state['timestamp']}",
    
    "type": "<response|explanation|suggestion|implementation|etc>",
    "certainty": "<high|medium|low>",
    "narrative_role": "<core|supportive|peripheral>",
    
    "concepts": ["concept_specific_1", "concept_2"],
    
    "block_metadata": {{
        "resource_url": "<URL exact dacă există>",
        "resource_type": "<documentation|api|guide|tool>",
        "resource_title": "<titlu>",
        "discussed_context": "<pentru ce e relevant>",
        
        "decision_choice": "<ce sugerează>",
        "decision_reason": "<DE CE>",
        "decision_alternatives": ["<alternative menționate>"],
        "decision_confidence": "<high|medium|low>",
        
        "doc_filename": "<nume fișier>",
        "doc_location": "<path>",
        "doc_purpose": "<scop>",
        "doc_key_settings": ["<setări>"]
    }}
}}

REGULI BLOCKS: (same as user)
- RESOURCE: URL present → extract all resource_* fields
- DECISION: suggests/recommends → extract decision_* fields
- DOCUMENT: file reference → extract doc_* fields
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
    """Stage 2a: Break USER semantic unit into atomic propositions WITH METADATA DUPLICATE."""

    import time
    start = time.time()

    su = state['user_semantic_unit']
    
    # Extract su_id for linking
    su_id = su.get('unit_id', state['user_message_id'])

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice și DUPLICĂ metadata.

UNITATEA SEMANTICĂ:
{json.dumps(su, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE:
═══════════════════════════════════════════════════════════════════

ATOMICITATE:
✅ O propoziție = O afirmație verificabilă
✅ 1-2 concepte principale per propoziție
✅ Auto-suficiente (înțelese fără context extern)
✅ Minimum 1, maximum 6 propositions

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitate
❌ NU defini conceptele
❌ NU genera cunoștințe generale

METADATA DUPLICATE:
✅ TOATE metadata din SU → duplicate în FIECARE propoziție
✅ type, certainty, block_metadata → toate copiate
✅ su_id = link către sursa

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (DOAR JSON array, fără ```):
═══════════════════════════════════════════════════════════════════

[
    {{
        "su_id": "{su_id}",
        "content": "<propoziție atomică auto-suficientă>",
        
        // METADATA DUPLICATE din SU
        "type": "{su.get('type', 'statement')}",
        "certainty": "{su.get('certainty', 'medium')}",
        "speaker": "user",
        
        // BLOCK METADATA duplicate (dacă există în SU)
        "block_metadata": {json.dumps(su.get('block_metadata', {}), ensure_ascii=False)},
        
        "concepts": ["concept1", "concept2"]
    }}
]

DEPTH CONTROL:
- Greeting SU → 0-1 props (minimal)
- Technical SU → 2-4 props (granular)
- Decision SU → 3-6 props (include reasoning as separate prop!)

CONCEPTS SPECIFICE:
- "webhook_retry_mechanism", "exponential_backoff_strategy"
- NU "webhook", "retry" (prea generic isolated)
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
    """Stage 2b: Break ASSISTANT semantic unit into atomic propositions WITH METADATA DUPLICATE."""

    import time
    start = time.time()

    su = state['assistant_semantic_unit']
    
    # Extract su_id for linking
    su_id = su.get('unit_id', state['assistant_message_id'])

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice și DUPLICĂ metadata.

UNITATEA SEMANTICĂ:
{json.dumps(su, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE:
═══════════════════════════════════════════════════════════════════

ATOMICITATE:
✅ O propoziție = O afirmație verificabilă
✅ 1-2 concepte principale per propoziție
✅ Auto-suficiente (înțelese fără context extern)
✅ Minimum 1, maximum 6 propositions

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitate
❌ NU defini conceptele
❌ NU genera cunoștințe generale

METADATA DUPLICATE:
✅ TOATE metadata din SU → duplicate în FIECARE propoziție
✅ type, certainty, block_metadata → toate copiate
✅ su_id = link către sursa

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (DOAR JSON array, fără ```):
═══════════════════════════════════════════════════════════════════

[
    {{
        "su_id": "{su_id}",
        "content": "<propoziție atomică auto-suficientă>",
        
        // METADATA DUPLICATE din SU
        "type": "{su.get('type', 'response')}",
        "certainty": "{su.get('certainty', 'medium')}",
        "speaker": "assistant",
        
        // BLOCK METADATA duplicate (dacă există în SU)
        "block_metadata": {json.dumps(su.get('block_metadata', {}), ensure_ascii=False)},
        
        "concepts": ["concept1", "concept2"]
    }}
]

DEPTH CONTROL:
- Greeting/confirmation → 0-1 props
- Technical explanation → 2-4 props
- Implementation/reasoning → 3-6 props (break down steps)
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





# Build the graph
workflow = StateGraph(BatchExtractionState)

# Add nodes
workflow.add_node("extract_user_su", extract_user_semantic_unit)
workflow.add_node("extract_assistant_su", extract_assistant_semantic_unit)
workflow.add_node("propositionalize_user", propositionalize_user)
workflow.add_node("propositionalize_assistant", propositionalize_assistant)

workflow.add_node("generate_embeddings", generate_embeddings)
workflow.add_node("store_propositions", store_propositions)
workflow.add_node("create_edges", create_edges)

# Define edges (parallel processing where possible)
workflow.set_entry_point("extract_user_su")
workflow.add_edge("extract_user_su", "extract_assistant_su")
workflow.add_edge("extract_assistant_su", "propositionalize_user")
workflow.add_edge("propositionalize_user", "propositionalize_assistant")
workflow.add_edge("propositionalize_assistant", "generate_embeddings")

workflow.add_edge("generate_embeddings", "store_propositions")
workflow.add_edge("store_propositions", "create_edges")
workflow.add_edge("create_edges", END)

# Compile the graph
graph = workflow.compile()

