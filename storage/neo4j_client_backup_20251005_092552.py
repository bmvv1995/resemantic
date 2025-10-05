"""
Neo4j Client for Living Knowledge Ecosystem

Handles all graph operations:
- Schema setup
- Proposition CRUD
- Edge creation (NEXT, COHERENT)
- Vector search
- Queries
"""

from neo4j import GraphDatabase
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


class Neo4jClient:
    """Neo4j database client with graph operations."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (bolt://...)
            user: Username
            password: Password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.uri = uri
        self.user = user

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =========================================================================
    # SCHEMA SETUP
    # =========================================================================

    def setup_schema(self):
        """
        Create schema: constraints, indexes, vector index.
        Idempotent (can run multiple times safely).
        """
        print("📐 Setting up Neo4j schema...")

        with self.driver.session() as session:
            # Constraints
            print("  ├─ Creating constraints...")
            session.run("""
                CREATE CONSTRAINT proposition_id_unique IF NOT EXISTS
                FOR (p:Proposition) REQUIRE p.id IS UNIQUE
            """)

            # Indexes
            print("  ├─ Creating indexes...")
            session.run("""
                CREATE INDEX proposition_timestamp IF NOT EXISTS
                FOR (p:Proposition) ON (p.timestamp)
            """)
            session.run("""
                CREATE INDEX proposition_speaker IF NOT EXISTS
                FOR (p:Proposition) ON (p.speaker)
            """)
            session.run("""
                CREATE INDEX proposition_coherence IF NOT EXISTS
                FOR (p:Proposition) ON (p.coherence_score)
            """)
            session.run("""
                CREATE INDEX proposition_is_weak IF NOT EXISTS
                FOR (p:Proposition) ON (p.is_weak)
            """)

            # Vector index
            print("  └─ Creating vector index...")
            session.run("""
                CREATE VECTOR INDEX proposition_embedding IF NOT EXISTS
                FOR (p:Proposition) ON (p.embedding)
                OPTIONS {
                  indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                  }
                }
            """)

        print("✅ Schema setup complete!\n")

    # =========================================================================
    # PROPOSITION CRUD
    # =========================================================================

    def create_proposition(
        self,
        content: str,
        embedding: List[float],
        type: str,
        certainty: str,
        concepts: List[str],
        source_message_id: str,
        source_semantic_unit_id: str,
        speaker: str,
        timestamp: str,
        proposition_id: Optional[str] = None,
        **extra_metadata
    ) -> Dict[str, Any]:
        """
        Create a new Proposition node.

        Args:
            content: Proposition text
            embedding: OpenAI embedding vector (1536 dims)
            type: "fact", "opinion", "question", etc.
            certainty: "high", "medium", "low"
            concepts: List of key concepts
            source_message_id: Original message ID
            source_semantic_unit_id: Stage 1 semantic unit ID
            speaker: "user" or "assistant"
            timestamp: ISO timestamp
            proposition_id: Optional UUID (generated if not provided)
            **extra_metadata: Future metadata fields

        Returns:
            Created proposition as dict
        """
        if not proposition_id:
            proposition_id = str(uuid.uuid4())

        now = datetime.now().isoformat()

        query = """
        CREATE (p:Proposition {
            id: $id,
            content: $content,
            embedding: $embedding,
            type: $type,
            certainty: $certainty,
            concepts: $concepts,
            source_message_id: $source_message_id,
            source_semantic_unit_id: $source_semantic_unit_id,
            speaker: $speaker,
            timestamp: datetime($timestamp),
            activation_count: 0,
            coherence_score: 0.5,
            is_weak: false,
            weakness_reason: null,
            last_accessed: null,
            created_at: datetime($now),
            updated_at: datetime($now)
        })
        RETURN p
        """

        params = {
            "id": proposition_id,
            "content": content,
            "embedding": embedding,
            "type": type,
            "certainty": certainty,
            "concepts": concepts,
            "source_message_id": source_message_id,
            "source_semantic_unit_id": source_semantic_unit_id,
            "speaker": speaker,
            "timestamp": timestamp,
            "now": now
        }

        # Add extra metadata
        params.update(extra_metadata)

        with self.driver.session() as session:
            result = session.run(query, params)
            record = result.single()

            if record:
                return dict(record['p'])
            else:
                raise Exception("Failed to create proposition")

    def get_proposition(self, proposition_id: str) -> Optional[Dict]:
        """Get proposition by ID."""
        query = """
        MATCH (p:Proposition {id: $id})
        RETURN p
        """

        with self.driver.session() as session:
            result = session.run(query, {"id": proposition_id})
            record = result.single()
            return dict(record['p']) if record else None

    def update_proposition(self, proposition_id: str, **updates):
        """
        Update proposition metadata.

        Args:
            proposition_id: Proposition ID
            **updates: Fields to update (e.g., coherence_score=0.8, is_weak=True)
        """
        # Build SET clause dynamically
        set_clauses = ", ".join([f"p.{key} = ${key}" for key in updates.keys()])
        set_clauses += ", p.updated_at = datetime($now)"

        query = f"""
        MATCH (p:Proposition {{id: $id}})
        SET {set_clauses}
        RETURN p
        """

        params = {"id": proposition_id, "now": datetime.now().isoformat()}
        params.update(updates)

        with self.driver.session() as session:
            result = session.run(query, params)
            record = result.single()
            return dict(record['p']) if record else None

    # =========================================================================
    # EDGE CREATION
    # =========================================================================

    def create_temporal_edge(self, from_id: str, to_id: str):
        """
        Create NEXT edge (temporal flow: from_id happened before to_id).

        Args:
            from_id: Source proposition ID
            to_id: Target proposition ID
        """
        query = """
        MATCH (from:Proposition {id: $from_id})
        MATCH (to:Proposition {id: $to_id})
        MERGE (from)-[r:NEXT {created_at: datetime($now)}]->(to)
        RETURN r
        """

        with self.driver.session() as session:
            session.run(query, {
                "from_id": from_id,
                "to_id": to_id,
                "now": datetime.now().isoformat()
            })

    def create_semantic_edge(
        self,
        prop1_id: str,
        prop2_id: str,
        weight: float,
        created_by: str = "extraction"
    ):
        """
        Create COHERENT edge (semantic similarity).

        Args:
            prop1_id: First proposition ID
            prop2_id: Second proposition ID
            weight: Exact cosine similarity (0-1)
            created_by: "extraction" or "sleep_cycle"
        """
        query = """
        MATCH (p1:Proposition {id: $prop1_id})
        MATCH (p2:Proposition {id: $prop2_id})
        MERGE (p1)-[r:COHERENT]-(p2)
        SET r.weight = $weight,
            r.created_at = datetime($now),
            r.created_by = $created_by,
            r.coactivation_count = coalesce(r.coactivation_count, 0),
            r.last_strengthened = null
        RETURN r
        """

        with self.driver.session() as session:
            session.run(query, {
                "prop1_id": prop1_id,
                "prop2_id": prop2_id,
                "weight": weight,
                "created_by": created_by,
                "now": datetime.now().isoformat()
            })

    # =========================================================================
    # VECTOR SEARCH
    # =========================================================================

    def vector_search(
        self,
        query_embedding: List[float],
        k: int = 10,
        min_similarity: float = 0.4
    ) -> List[Dict]:
        """
        Semantic search using vector similarity.

        Args:
            query_embedding: Query vector (1536 dims)
            k: Number of results
            min_similarity: Minimum cosine similarity threshold

        Returns:
            List of propositions with similarity scores
        """
        query = """
        CALL db.index.vector.queryNodes(
            'proposition_embedding',
            $k,
            $query_embedding
        )
        YIELD node, score
        WHERE score >= $min_similarity
        RETURN node.id AS id,
               node.content AS content,
               node.speaker AS speaker,
               node.type AS type,
               node.concepts AS concepts,
               node.coherence_score AS coherence_score,
               node.is_weak AS is_weak,
               score AS similarity
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            result = session.run(query, {
                "query_embedding": query_embedding,
                "k": k,
                "min_similarity": min_similarity
            })

            return [dict(record) for record in result]

    # =========================================================================
    # QUERIES
    # =========================================================================

    def count_propositions(self) -> int:
        """Count total propositions."""
        with self.driver.session() as session:
            result = session.run("MATCH (p:Proposition) RETURN count(p) AS count")
            return result.single()['count']

    def count_edges(self) -> Dict[str, int]:
        """Count edges by type."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS edge_type, count(r) AS count
            """)
            return {record['edge_type']: record['count'] for record in result}

    def get_all_propositions(self, limit: int = 100) -> List[Dict]:
        """Get all propositions (for debugging)."""
        query = """
        MATCH (p:Proposition)
        RETURN p
        ORDER BY p.created_at DESC
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, {"limit": limit})
            return [dict(record['p']) for record in result]

    def get_temporal_chain(self) -> Dict:
        """Get the temporal chain info (start, end, length)."""
        query = """
        MATCH path = (start:Proposition)-[:NEXT*]->(end:Proposition)
        WHERE NOT exists((start)<-[:NEXT]-())
        RETURN length(path) AS chain_length,
               start.content AS first_content,
               end.content AS last_content,
               start.timestamp AS first_time,
               end.timestamp AS last_time
        ORDER BY chain_length DESC
        LIMIT 1
        """

        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            return dict(record) if record else {}

    def get_semantic_neighbors(self, proposition_id: str, min_weight: float = 0.5) -> List[Dict]:
        """
        Get semantic neighbors of a proposition.

        Args:
            proposition_id: Proposition ID
            min_weight: Minimum edge weight

        Returns:
            List of neighbor propositions with weights
        """
        query = """
        MATCH (p:Proposition {id: $id})-[r:COHERENT]-(neighbor:Proposition)
        WHERE r.weight >= $min_weight
        RETURN neighbor.id AS id,
               neighbor.content AS content,
               r.weight AS similarity
        ORDER BY r.weight DESC
        """

        with self.driver.session() as session:
            result = session.run(query, {
                "id": proposition_id,
                "min_weight": min_weight
            })
            return [dict(record) for record in result]
