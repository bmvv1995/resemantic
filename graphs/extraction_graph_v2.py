"""
Extraction Graph V2 - Optimized Pipeline
=========================================

Key changes from V1:
1. Only 2 extraction stages (user + reasoning)
2. Assistant message stored RAW, not extracted
3. Faster: 2 LLM calls instead of 3
4. Clearer: facts vs logic separation

Flow:
User message → extract facts → propositionalize
Reasoning → extract logic → propositionalize
Assistant message → store RAW only
All → embeddings → storage → edges
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from datetime import datetime
import uuid

from config import ExtractionConfig
from graphs.extraction_nodes_v2 import (
    extract_user_v2,
    extract_reasoning_v2,
    propositionalize_user_v2,
    propositionalize_reasoning_v2
)
from graphs.storage_nodes import (
    generate_embeddings,
    store_propositions,
    create_edges
)


# ============================================
# STATE DEFINITION V2
# ============================================

class ExtractionStateV2(TypedDict):
    # Input
    user_message: str
    assistant_message: str
    assistant_reasoning: str  # CRITICAL for V2!
    conversation_history: List[Dict]
    timestamp: str
    user_message_id: str
    assistant_message_id: str
    
    # Stage 1: Semantic Units
    user_semantic_unit: Dict
    reasoning_semantic_unit: Dict  # Replaces assistant_semantic_unit
    
    # Stage 2: Propositions
    user_propositions: List[Dict]
    reasoning_propositions: List[Dict]  # Replaces assistant_propositions
    all_propositions: List[Dict]
    
    # Stage 3: Embeddings & Storage
    proposition_embeddings: List[List[float]]
    stored_proposition_ids: List[str]
    
    # Timing
    stage1_user_time: float
    stage1_reasoning_time: float  # Replaces stage1_assistant_time
    stage2_user_time: float
    stage2_reasoning_time: float  # Replaces stage2_assistant_time
    embedding_time: float
    storage_time: float
    edge_creation_time: float
    
    # Error handling
    error: str


# ============================================
# BUILD GRAPH V2
# ============================================

workflow = StateGraph(ExtractionStateV2)

# Stage 1: Extract semantic units
workflow.add_node("extract_user", extract_user_v2)
workflow.add_node("extract_reasoning", extract_reasoning_v2)

# Stage 2: Propositionalize
workflow.add_node("propositionalize_user", propositionalize_user_v2)
workflow.add_node("propositionalize_reasoning", propositionalize_reasoning_v2)

# Stage 3: Storage (reuse from V1)
workflow.add_node("generate_embeddings", generate_embeddings)
workflow.add_node("store_propositions", store_propositions)
workflow.add_node("create_edges", create_edges)

# Flow
workflow.set_entry_point("extract_user")

# Stage 1 parallel execution
workflow.add_edge("extract_user", "extract_reasoning")

# Stage 2 parallel execution
workflow.add_edge("extract_reasoning", "propositionalize_user")
workflow.add_edge("propositionalize_user", "propositionalize_reasoning")

# Stage 3 sequential
workflow.add_edge("propositionalize_reasoning", "generate_embeddings")
workflow.add_edge("generate_embeddings", "store_propositions")
workflow.add_edge("store_propositions", "create_edges")
workflow.add_edge("create_edges", END)

# Compile
graph_v2 = workflow.compile()


# ============================================
# CONVENIENCE WRAPPER
# ============================================

def invoke_clean_v2(batch_input: dict) -> dict:
    """
    Invoke V2 extraction graph and return CLEAN result.
    
    Same as V1 invoke_clean but for V2 graph.
    """
    result = graph_v2.invoke(batch_input)
    
    # Remove embeddings (storage concern, not output)
    return {k: v for k, v in result.items() if k != 'proposition_embeddings'}


# Export
__all__ = ['graph_v2', 'invoke_clean_v2']
