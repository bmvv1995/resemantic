"""
ReSemantic Configuration
Centralized configuration for extraction, storage, and graph parameters.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════════
# EXTRACTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class ExtractionConfig:
    """Configuration for semantic extraction pipeline."""

    # LLM Model
    LLM_MODEL = "claude-3-5-haiku-20241022"
    LLM_TEMPERATURE = 0.3
    LLM_MAX_TOKENS = 1500

    # Context
    CONTEXT_MAX_MESSAGES = 2  # Number of previous messages to include as context

    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


# ═══════════════════════════════════════════════════════════════════
# CHAT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class ChatConfig:
    """Configuration for chat interface."""

    # Chat Model (can use different model than extraction)
    CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-3-5-haiku-20241022")
    CHAT_TEMPERATURE = 0.7

    # Reasoning Display
    ENABLE_REASONING_DISPLAY = os.getenv("ENABLE_REASONING", "false").lower() == "true"
    REASONING_MODEL = "claude-3-5-sonnet-20241022"  # Model with extended thinking support


# ═══════════════════════════════════════════════════════════════════
# EMBEDDING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class EmbeddingConfig:
    """Configuration for embedding generation."""

    # Model
    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536

    # API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BATCH_SIZE = 100  # Max embeddings per batch request


# ═══════════════════════════════════════════════════════════════════
# NEO4J CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class Neo4jConfig:
    """Configuration for Neo4j graph database."""

    # Connection
    URI = "bolt://172.105.85.181:7687"
    USER = "neo4j"
    PASSWORD = "test1234"

    # Graph Structure
    SIMILARITY_THRESHOLD = 0.4  # Minimum similarity for COHERENT edges
    TOP_K_NEIGHBORS = 10  # Maximum semantic neighbors per proposition

    # Edge Types
    TEMPORAL_EDGE = "NEXT"
    SEMANTIC_EDGE = "COHERENT"


# ═══════════════════════════════════════════════════════════════════
# SQLITE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class SQLiteConfig:
    """Configuration for SQLite archival storage."""

    DATABASE_PATH = "data/resemantic_archive.db"


# ═══════════════════════════════════════════════════════════════════
# LANGSMITH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

class LangSmithConfig:
    """Configuration for LangSmith tracing."""

    TRACING_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    API_KEY = os.getenv("LANGCHAIN_API_KEY")
    PROJECT = os.getenv("LANGCHAIN_PROJECT", "resemantic-extraction")
    ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")


# ═══════════════════════════════════════════════════════════════════
# EXPORT ALL CONFIGS
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    'ExtractionConfig',
    'ChatConfig',
    'EmbeddingConfig',
    'Neo4jConfig',
    'SQLiteConfig',
    'LangSmithConfig'
]

# ============================================
# EXTRACTION VERSION CONTROL
# ============================================

class ExtractionVersion:
    """
    Control which extraction pipeline to use.
    
    V1 (original):
    - Extract from user message
    - Extract from assistant message
    - Extract from assistant reasoning (if available)
    
    V2 (optimized):
    - Extract from user message (FACTS focus)
    - Extract from reasoning ONLY (LOGIC focus)
    - Assistant message: RAW storage, NO extraction
    
    Benefits V2:
    - 33% faster (2 LLM calls vs 3)
    - Zero redundancy (reasoning contains all semantic)
    - Richer context (reasoning has WHY, alternatives, drifts)
    - Clearer separation (facts vs logic)
    """
    
    # Toggle extraction version
    VERSION = "v1"  # Options: "v1", "v2"
    
    # V2 specific settings
    V2_USER_FOCUS = "facts, URLs, technical specs, concrete data"
    V2_REASONING_FOCUS = "interpretations, decisions, alternatives, drifts"
    
    @classmethod
    def is_v2(cls):
        return cls.VERSION == "v2"
    
    @classmethod
    def get_version(cls):
        return cls.VERSION

