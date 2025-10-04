"""
Neo4j Schema Definitions for Living Knowledge Ecosystem

Schema Philosophy:
- Flexible metadata (add fields as discovered, no breaking changes)
- Proposition nodes (atomic semantic units)
- Temporal + Semantic edges (conversation flow + coherence)
- No deletions (weak nodes marked in metadata)
"""

# =============================================================================
# SCHEMA CREATION QUERIES
# =============================================================================

CREATE_CONSTRAINTS = """
-- Unique constraint on Proposition ID
CREATE CONSTRAINT proposition_id_unique IF NOT EXISTS
FOR (p:Proposition) REQUIRE p.id IS UNIQUE;
"""

CREATE_INDEXES = """
-- Index on timestamp for temporal queries
CREATE INDEX proposition_timestamp IF NOT EXISTS
FOR (p:Proposition) ON (p.timestamp);

-- Index on speaker for filtering
CREATE INDEX proposition_speaker IF NOT EXISTS
FOR (p:Proposition) ON (p.speaker);

-- Index on coherence_score for relevance queries
CREATE INDEX proposition_coherence IF NOT EXISTS
FOR (p:Proposition) ON (p.coherence_score);

-- Index on is_weak for filtering weak nodes
CREATE INDEX proposition_is_weak IF NOT EXISTS
FOR (p:Proposition) ON (p.is_weak);
"""

CREATE_VECTOR_INDEX = """
-- Vector index for embedding similarity search
-- Using cosine similarity for semantic matching
CREATE VECTOR INDEX proposition_embedding IF NOT EXISTS
FOR (p:Proposition) ON (p.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
};
"""

# =============================================================================
# NODE SCHEMA (Documentation)
# =============================================================================

PROPOSITION_SCHEMA = {
    "label": "Proposition",
    "description": "Atomic semantic unit from conversational extraction",
    "properties": {
        # Core
        "id": {
            "type": "STRING (UUID)",
            "required": True,
            "description": "Unique identifier"
        },
        "content": {
            "type": "STRING",
            "required": True,
            "description": "Atomic proposition text (self-contained)"
        },
        "embedding": {
            "type": "VECTOR[1536]",
            "required": True,
            "description": "OpenAI text-embedding-3-small vector"
        },

        # Extraction metadata (from Stage 2)
        "type": {
            "type": "STRING",
            "required": True,
            "values": ["fact", "opinion", "question", "command", "agreement", "decision"],
            "description": "Proposition type"
        },
        "certainty": {
            "type": "STRING",
            "required": True,
            "values": ["high", "medium", "low"],
            "description": "Certainty level"
        },
        "concepts": {
            "type": "LIST[STRING]",
            "required": False,
            "description": "Key concepts mentioned"
        },

        # Source tracking
        "source_message_id": {
            "type": "STRING",
            "required": True,
            "description": "Original message ID"
        },
        "source_semantic_unit_id": {
            "type": "STRING",
            "required": True,
            "description": "Stage 1 semantic unit ID (traceability)"
        },
        "speaker": {
            "type": "STRING",
            "required": True,
            "values": ["user", "assistant"],
            "description": "Who said it"
        },
        "timestamp": {
            "type": "DATETIME",
            "required": True,
            "description": "When it was said"
        },

        # Relevance metadata (for sleep & retrieval)
        "activation_count": {
            "type": "INTEGER",
            "default": 0,
            "description": "How many times retrieved"
        },
        "coherence_score": {
            "type": "FLOAT",
            "default": 0.5,
            "description": "Graph-based relevance (updated by sleep cycles)"
        },
        "is_weak": {
            "type": "BOOLEAN",
            "default": False,
            "description": "Marked as weak (low relevance, not deleted)"
        },
        "weakness_reason": {
            "type": "STRING",
            "default": None,
            "description": "Why marked weak (e.g., 'low_coherence', 'rarely_used')"
        },
        "last_accessed": {
            "type": "DATETIME",
            "default": None,
            "description": "Last retrieval timestamp"
        },

        # Lifecycle
        "created_at": {
            "type": "DATETIME",
            "required": True,
            "description": "Creation timestamp"
        },
        "updated_at": {
            "type": "DATETIME",
            "required": True,
            "description": "Last update timestamp"
        },

        # Future metadata (added dynamically, no schema change needed)
        # Examples:
        # - domain: STRING (e.g., "medical", "finance")
        # - pattern_type: STRING (discovered patterns)
        # - semantic_cluster: STRING (cluster ID)
        # - quality_score: FLOAT (user feedback)
    }
}

# =============================================================================
# EDGE SCHEMAS (Documentation)
# =============================================================================

NEXT_EDGE_SCHEMA = {
    "type": "NEXT",
    "direction": "DIRECTED",
    "description": "Temporal flow in conversation (p1 said before p2)",
    "properties": {
        "created_at": {
            "type": "DATETIME",
            "required": True,
            "description": "When edge was created"
        }
    }
}

COHERENT_EDGE_SCHEMA = {
    "type": "COHERENT",
    "direction": "UNDIRECTED",
    "description": "Semantic similarity between propositions",
    "properties": {
        "weight": {
            "type": "FLOAT",
            "required": True,
            "description": "Exact cosine similarity (0-1), used for traversal filtering"
        },
        "created_at": {
            "type": "DATETIME",
            "required": True,
            "description": "When edge was created"
        },
        "created_by": {
            "type": "STRING",
            "values": ["extraction", "sleep_cycle"],
            "default": "extraction",
            "description": "Who created the edge"
        },
        "coactivation_count": {
            "type": "INTEGER",
            "default": 0,
            "description": "How many times co-retrieved (updated by sleep)"
        },
        "last_strengthened": {
            "type": "DATETIME",
            "default": None,
            "description": "Last time weight was increased"
        }
    }
}

# =============================================================================
# SAMPLE QUERIES (for validation)
# =============================================================================

SAMPLE_QUERIES = {
    "count_propositions": """
        MATCH (p:Proposition)
        RETURN count(p) AS total
    """,

    "count_edges": """
        MATCH ()-[r]->()
        RETURN type(r) AS edge_type, count(r) AS count
    """,

    "temporal_chain": """
        MATCH path = (start:Proposition)-[:NEXT*]->(end:Proposition)
        WHERE NOT exists((start)<-[:NEXT]-())
        RETURN length(path) AS chain_length,
               start.content AS first,
               end.content AS last
        ORDER BY chain_length DESC
        LIMIT 1
    """,

    "semantic_neighbors": """
        MATCH (p:Proposition)-[r:COHERENT]-(neighbor)
        RETURN p.id, p.content,
               count(neighbor) AS neighbor_count,
               avg(r.weight) AS avg_weight
        ORDER BY neighbor_count DESC
        LIMIT 10
    """,

    "weak_propositions": """
        MATCH (p:Proposition)
        WHERE p.is_weak = true
        RETURN p.id, p.content, p.weakness_reason, p.coherence_score
    """,

    "sample_proposition": """
        MATCH (p:Proposition)
        RETURN p
        LIMIT 1
    """
}
