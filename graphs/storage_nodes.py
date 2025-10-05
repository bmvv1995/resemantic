"""
Storage nodes for ReSemantic extraction graph.
Split into 3 separate responsibilities:
1. generate_embeddings - Create embeddings for propositions
2. store_propositions - Store in Neo4j + SQLite
3. create_edges - Create temporal + semantic edges
"""

from typing import Dict
from storage import Neo4jClient, ArchiveDB, EmbeddingGenerator
from config import Neo4jConfig, EmbeddingConfig


def generate_embeddings(state: dict) -> Dict:
    """Node 1: Generate embeddings for all propositions.

    Input: user_propositions, assistant_propositions
    Output: all_propositions (with metadata), proposition_embeddings
    """
    import time
    start = time.time()

    try:
        # Initialize embedding generator
        embedder = EmbeddingGenerator()

        # Collect all propositions with speaker metadata
        all_props = []

        for prop in state.get('user_propositions', []):
            all_props.append({
                **prop,
                'speaker': 'user',
                'message_id': state['user_message_id'],
                'semantic_unit_id': state['user_semantic_unit']['unit_id']
            })

        for prop in state.get('assistant_propositions', []):
            all_props.append({
                **prop,
                'speaker': 'assistant',
                'message_id': state['assistant_message_id'],
                'semantic_unit_id': state['assistant_semantic_unit']['unit_id']
            })

        # Generate embeddings (batch)
        prop_texts = [p['content'] for p in all_props]
        embeddings = embedder.generate_batch(prop_texts) if prop_texts else []

        return {
            "all_propositions": all_props,
            "proposition_embeddings": embeddings,
            "embedding_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Embedding error: {str(e)}",
            "all_propositions": [],
            "proposition_embeddings": [],
            "embedding_time": time.time() - start
        }


def store_propositions(state: dict) -> Dict:
    """Node 2: Store propositions in Neo4j + SQLite archive.

    Input: all_propositions, proposition_embeddings
    Output: stored_proposition_ids
    """
    import time
    start = time.time()

    # Initialize storage clients
    neo4j = Neo4jClient(
        uri=Neo4jConfig.URI,
        user=Neo4jConfig.USER,
        password=Neo4jConfig.PASSWORD
    )

    archive = ArchiveDB()
    stored_ids = []

    try:
        # 1. Store messages in archive
        archive.store_message(
            state['user_message_id'],
            "user",
            state['user_message'],
            state['timestamp']
        )

        archive.store_message(
            state['assistant_message_id'],
            "assistant",
            state['assistant_message'],
            state['timestamp']
        )

        # 1.5 Store reasoning if available (as special message in archive)
        if state.get('assistant_reasoning'):
            archive.store_message(
                f"{state['assistant_message_id']}_reasoning",
                "assistant_reasoning",
                state['assistant_reasoning'],
                state['timestamp']
            )

        # 2. Store semantic units in archive
        archive.store_semantic_unit(
            state['user_semantic_unit']['unit_id'],
            state['user_message_id'],
            state['user_semantic_unit']['content'],
            state['user_semantic_unit']
        )

        archive.store_semantic_unit(
            state['assistant_semantic_unit']['unit_id'],
            state['assistant_message_id'],
            state['assistant_semantic_unit']['content'],
            state['assistant_semantic_unit']
        )

        # 3. Store propositions in Neo4j + archive
        all_props = state.get('all_propositions', [])
        embeddings = state.get('proposition_embeddings', [])

        for prop, embedding in zip(all_props, embeddings):
            # Create in Neo4j
            neo_prop = neo4j.create_proposition(
                content=prop['content'],
                embedding=embedding,
                type=prop['type'],
                certainty=prop['certainty'],
                concepts=prop.get('concepts', []),
                source_message_id=prop['message_id'],
                source_semantic_unit_id=prop['semantic_unit_id'],
                speaker=prop['speaker'],
                timestamp=state['timestamp'],
                block_metadata=prop.get('block_metadata', {})
            )

            prop_id = neo_prop['id']
            stored_ids.append(prop_id)

            # Archive proposition
            archive.store_proposition(
                prop_id,
                prop['semantic_unit_id'],
                prop['content'],
                prop
            )

        return {
            "stored_proposition_ids": stored_ids,
            "storage_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Storage error: {str(e)}",
            "stored_proposition_ids": [],
            "storage_time": time.time() - start
        }

    finally:
        neo4j.close()
        archive.close()


def create_edges(state: dict) -> Dict:
    """Node 3: Create temporal (NEXT) and semantic (COHERENT) edges.

    Input: stored_proposition_ids, proposition_embeddings
    Output: edge_creation_time
    """
    import time
    start = time.time()

    # Initialize Neo4j client
    neo4j = Neo4jClient(
        uri=Neo4jConfig.URI,
        user=Neo4jConfig.USER,
        password=Neo4jConfig.PASSWORD
    )

    try:
        stored_ids = state.get('stored_proposition_ids', [])
        embeddings = state.get('proposition_embeddings', [])

        # 1. Create temporal edges (NEXT)
        prev_prop_id = None
        for prop_id in stored_ids:
            if prev_prop_id:
                neo4j.create_temporal_edge(prev_prop_id, prop_id)
            prev_prop_id = prop_id

        # 2. Create semantic edges (COHERENT)
        # Link each proposition to its top-K most similar neighbors
        for prop_id, embedding in zip(stored_ids, embeddings):
            # Vector search for similar propositions
            similar = neo4j.vector_search(
                query_embedding=embedding,
                k=Neo4jConfig.TOP_K_NEIGHBORS + 1,  # +1 because it includes self
                min_similarity=Neo4jConfig.SIMILARITY_THRESHOLD
            )

            # Create edges to top neighbors (excluding self)
            for neighbor in similar:
                if neighbor['id'] == prop_id:
                    continue  # Skip self

                # Create semantic edge with exact similarity weight
                neo4j.create_semantic_edge(
                    prop_id,
                    neighbor['id'],
                    weight=neighbor['similarity'],
                    created_by="extraction"
                )

        return {
            "edge_creation_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Edge creation error: {str(e)}",
            "edge_creation_time": time.time() - start
        }

    finally:
        neo4j.close()
