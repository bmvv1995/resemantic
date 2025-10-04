"""
Test Complete Integration: Embeddings + Neo4j + SQLite
"""
from storage import Neo4jClient, ArchiveDB, EmbeddingGenerator, cosine_similarity
from dotenv import load_dotenv
import os

load_dotenv()

# Connection details
NEO4J_URI = "bolt://172.105.85.181:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "test1234"

def test_complete_integration():
    """Test end-to-end storage with real embeddings."""

    print("="*70)
    print("COMPLETE INTEGRATION TEST")
    print("="*70 + "\n")

    # Initialize all components
    print("🔧 Initializing components...")
    embedder = EmbeddingGenerator()
    neo4j = Neo4jClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    archive = ArchiveDB()

    print(f"✅ Embedder: {embedder.model} ({embedder.dimensions} dims)")
    print(f"✅ Neo4j: {neo4j.uri}")
    print(f"✅ SQLite: {archive.db_path}\n")

    # Test data
    test_message = {
        "id": "msg_test_001",
        "role": "user",
        "content": "buna. ce inseamna pentru tine o unitate semantica?",
        "timestamp": "2025-10-04T12:00:00Z"
    }

    test_semantic_unit = {
        "unit_id": "unit_test_001",
        "content": "User-ul salută și întreabă ce înseamnă o unitate semantică",
        "type": "question",
        "narrative_role": "core",
        "concepts": ["unitate semantică", "definiție"]
    }

    test_propositions = [
        {
            "content": "User salută",
            "type": "fact",
            "certainty": "high",
            "concepts": ["salut"]
        },
        {
            "content": "User întreabă ce înseamnă o unitate semantică",
            "type": "question",
            "certainty": "high",
            "concepts": ["unitate semantică", "definiție"]
        }
    ]

    # 1. Store in Archive (SQLite)
    print("📦 Storing in SQLite archive...")
    archive.store_message(
        test_message['id'],
        test_message['role'],
        test_message['content'],
        test_message['timestamp']
    )

    archive.store_semantic_unit(
        test_semantic_unit['unit_id'],
        test_message['id'],
        test_semantic_unit['content'],
        test_semantic_unit
    )
    print("✅ Archive stored\n")

    # 2. Generate embeddings
    print("🧠 Generating embeddings...")
    prop_texts = [p['content'] for p in test_propositions]
    embeddings = embedder.generate_batch(prop_texts)
    print(f"✅ Generated {len(embeddings)} embeddings ({len(embeddings[0])} dims each)\n")

    # 3. Store propositions in Neo4j
    print("📊 Storing propositions in Neo4j...")
    neo4j_prop_ids = []

    for i, (prop, embedding) in enumerate(zip(test_propositions, embeddings)):
        # Create in Neo4j
        neo_prop = neo4j.create_proposition(
            content=prop['content'],
            embedding=embedding,
            type=prop['type'],
            certainty=prop['certainty'],
            concepts=prop['concepts'],
            source_message_id=test_message['id'],
            source_semantic_unit_id=test_semantic_unit['unit_id'],
            speaker=test_message['role'],
            timestamp=test_message['timestamp']
        )

        neo4j_prop_ids.append(neo_prop['id'])
        print(f"   ✅ Proposition {i+1}: {neo_prop['id'][:8]}...")

        # Archive proposition
        archive.store_proposition(
            neo_prop['id'],
            test_semantic_unit['unit_id'],
            prop['content'],
            prop
        )

    print()

    # 4. Create temporal edge
    print("🔗 Creating temporal edge (NEXT)...")
    neo4j.create_temporal_edge(neo4j_prop_ids[0], neo4j_prop_ids[1])
    print("✅ Temporal edge created\n")

    # 5. Create semantic edge (using embedding similarity)
    print("🔗 Creating semantic edge (COHERENT)...")
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    neo4j.create_semantic_edge(
        neo4j_prop_ids[0],
        neo4j_prop_ids[1],
        weight=similarity,
        created_by="extraction"
    )
    print(f"✅ Semantic edge created (weight: {similarity:.4f})\n")

    # 6. Test vector search
    print("🔍 Testing vector search...")
    query_text = "ce sunt unitățile semantice?"
    query_embedding = embedder.generate(query_text)

    results = neo4j.vector_search(
        query_embedding=query_embedding,
        k=5,
        min_similarity=0.3
    )

    print(f"Query: '{query_text}'")
    print(f"Results found: {len(results)}\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']}")
        print(f"   Similarity: {result['similarity']:.4f}")
        print(f"   Type: {result['type']}, Speaker: {result['speaker']}\n")

    # 7. Test traceability (SQLite)
    print("🔗 Testing traceability (SQLite lineage)...")
    lineage = archive.get_full_lineage(neo4j_prop_ids[1])

    print("Lineage chain:")
    print(f"📨 Message: {lineage['message']['content'][:50]}...")
    print(f"📝 Semantic Unit: {lineage['semantic_unit']['content'][:50]}...")
    print(f"⚛️  Proposition: {lineage['proposition']['content']}\n")

    # 8. Stats
    print("📊 Final Statistics:")
    print(f"Neo4j:")
    print(f"   Propositions: {neo4j.count_propositions()}")
    print(f"   Edges: {neo4j.count_edges()}")

    print(f"SQLite:")
    stats = archive.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()

    print("="*70)
    print("✅ COMPLETE INTEGRATION WORKING!")
    print("="*70)
    print("\n🎯 Ready for:")
    print("   - Extraction graph integration")
    print("   - End-to-end pipeline testing")
    print("   - Conversation batch processing")

    # Cleanup
    neo4j.close()
    archive.close()

if __name__ == "__main__":
    test_complete_integration()
