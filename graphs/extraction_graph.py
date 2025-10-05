"""
ReSemantic Extraction Pipeline - CLEAN VERSION (zero redundancy)
WITH METADATA BLOCKS (resource, decision, document)
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import json
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Neo4jClient, ArchiveDB, EmbeddingGenerator, cosine_similarity
from config import ExtractionConfig, EmbeddingConfig, Neo4jConfig, SQLiteConfig
from graphs.storage_nodes import generate_embeddings, store_propositions, create_edges

load_dotenv()


class BatchExtractionState(TypedDict):
    """State for batch extraction of conversation pair."""
    user_message: str
    assistant_message: str
    assistant_reasoning: str
    conversation_history: List[Dict]
    timestamp: str
    user_message_id: str
    assistant_message_id: str
    user_semantic_unit: Dict
    assistant_semantic_unit: Dict
    user_propositions: List[Dict]
    assistant_propositions: List[Dict]
    all_propositions: List[Dict]
    proposition_embeddings: List[List[float]]
    stage1_user_time: float
    stage1_assistant_time: float
    stage2_user_time: float
    stage2_assistant_time: float
    embedding_time: float
    storage_time: float
    edge_creation_time: float
    error: str
    stored_proposition_ids: List[str]


llm = ChatAnthropic(
    model=ExtractionConfig.LLM_MODEL,
    temperature=ExtractionConfig.LLM_TEMPERATURE,
    max_tokens=ExtractionConfig.LLM_MAX_TOKENS,
    api_key=ExtractionConfig.ANTHROPIC_API_KEY
)


def build_context_from_history(history: List[Dict], max_messages: int = None) -> str:
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
    """Stage 1a: Extract semantic unit + blocks for USER message."""
    import time
    import json as json_lib
    start = time.time()

    context = build_context_from_history(state.get('conversation_history', []))

    prompt = f"""You are a conversation analyzer. Extract semantic unit with blocks.

CONTEXT:
{context}

MESSAGE:
Speaker: user
Time: {state['timestamp']}
Content: {json_lib.dumps(state['user_message'], ensure_ascii=False)}

TASK:
1. Reformulate with context (resolve references: "da" → "User confirms X")
2. Detect type and extract relevant blocks
3. Return ONLY JSON (no markdown):

{{
    "unit_id": "{state['user_message_id']}",
    "content": "clear reformulation with resolved context",
    "speaker": "user",
    "timestamp": "{state['timestamp']}",
    "type": "decision|resource|document|question|statement|confirmation",
    "certainty": "high|medium|low",
    "narrative_role": "core|supportive|peripheral",
    "concepts": ["specific_concept1", "concept2"],
    "block_metadata": {{
        "resource_url": "exact URL if present",
        "resource_type": "docs|api|guide|tool",
        "resource_title": "title from context",
        "discussed_context": "why relevant",
        
        "decision_choice": "what was decided",
        "decision_reason": "WHY (REQUIRED for decisions)",
        "decision_alternatives": ["rejected options"],
        "decision_confidence": "high|medium|low",
        
        "doc_filename": "file name",
        "doc_location": "full path",
        "doc_purpose": "what it's for",
        "doc_key_settings": ["settings if config"]
    }}
}}

BLOCKS RULES (set only relevant fields for type):
- resource: url (required), type, title, context
- decision: choice, reason/WHY (REQUIRED), alternatives, confidence  
- document: filename, location, purpose, settings

CONCEPTS: Specific compound terms (webhook_retry, API_auth), not generic words.
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()
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
    """Stage 1b: Extract semantic unit + blocks for ASSISTANT message."""
    import time
    import json as json_lib
    start = time.time()

    context_messages = list(state.get('conversation_history', []))
    context_messages.append({"role": "user", "content": state['user_message']})
    context = build_context_from_history(context_messages)

    reasoning_note = ""
    if state.get('assistant_reasoning'):
        reasoning_note = f"\n\nReasoning: {state['assistant_reasoning']}"

    prompt = f"""You are a conversation analyzer. Extract semantic unit with blocks.

CONTEXT:
{context}

MESSAGE:
Speaker: assistant
Time: {state['timestamp']}
Content: {json_lib.dumps(state['assistant_message'], ensure_ascii=False)}{reasoning_note}

TASK:
Return ONLY JSON (no markdown):

{{
    "unit_id": "{state['assistant_message_id']}",
    "content": "description of assistant response",
    "speaker": "assistant",
    "timestamp": "{state['timestamp']}",
    "type": "response|explanation|suggestion|implementation",
    "certainty": "high|medium|low",
    "narrative_role": "core|supportive|peripheral",
    "concepts": ["specific_concept1", "concept2"],
    "block_metadata": {{
        "resource_url": "...",
        "resource_type": "...",
        "decision_choice": "...",
        "decision_reason": "...",
        "doc_filename": "...",
        "doc_location": "..."
    }}
}}

Set only relevant block fields for message type.
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()
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

    su = state['user_semantic_unit']
    su_id = su.get('unit_id', state['user_message_id'])

    prompt = f"""Break semantic unit into atomic propositions.

SEMANTIC UNIT:
{json.dumps(su, indent=2, ensure_ascii=False)}

Return ONLY JSON array (no markdown):

[
    {{
        "su_id": "{su_id}",
        "content": "atomic self-contained proposition",
        "type": "{su.get('type', 'statement')}",
        "certainty": "{su.get('certainty', 'medium')}",
        "block_metadata": {json.dumps(su.get('block_metadata', {}), ensure_ascii=False)},
        "concepts": ["concept1", "concept2"]
    }}
]

RULES:
- 1 proposition = 1 verifiable statement
- Self-contained (understandable without external context)
- 1-2 core concepts per proposition
- Min 1, max 6 propositions
- NO hallucination - only decompose what's in the unit
- Props INHERIT all metadata (type, certainty, blocks) from SU via su_id

CONCEPTS: Specific compound terms (webhook_retry_mechanism), not isolated generic words.
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()
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

    su = state['assistant_semantic_unit']
    su_id = su.get('unit_id', state['assistant_message_id'])

    prompt = f"""Break semantic unit into atomic propositions.

SEMANTIC UNIT:
{json.dumps(su, indent=2, ensure_ascii=False)}

Return ONLY JSON array (no markdown):

[
    {{
        "su_id": "{su_id}",
        "content": "atomic self-contained proposition",
        "type": "{su.get('type', 'response')}",
        "certainty": "{su.get('certainty', 'medium')}",
        "block_metadata": {json.dumps(su.get('block_metadata', {}), ensure_ascii=False)},
        "concepts": ["concept1", "concept2"]
    }}
]

RULES:
- 1 proposition = 1 verifiable statement
- Self-contained (understandable without external context)
- Min 1, max 6 propositions
- NO hallucination - only decompose what's in the unit
- Props INHERIT all metadata from SU via su_id
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()
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

workflow.add_node("extract_user_su", extract_user_semantic_unit)
workflow.add_node("extract_assistant_su", extract_assistant_semantic_unit)
workflow.add_node("propositionalize_user", propositionalize_user)
workflow.add_node("propositionalize_assistant", propositionalize_assistant)
workflow.add_node("generate_embeddings", generate_embeddings)
workflow.add_node("store_propositions", store_propositions)
workflow.add_node("create_edges", create_edges)

workflow.set_entry_point("extract_user_su")
workflow.add_edge("extract_user_su", "extract_assistant_su")
workflow.add_edge("extract_assistant_su", "propositionalize_user")
workflow.add_edge("propositionalize_user", "propositionalize_assistant")
workflow.add_edge("propositionalize_assistant", "generate_embeddings")
workflow.add_edge("generate_embeddings", "store_propositions")
workflow.add_edge("store_propositions", "create_edges")
workflow.add_edge("create_edges", END)

graph = workflow.compile()
