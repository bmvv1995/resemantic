"""
Test Neo4j Schema Setup
"""
from storage.neo4j_client import Neo4jClient

# Connection details
URI = "bolt://172.105.85.181:7687"
USER = "neo4j"
PASSWORD = "test1234"

def test_schema():
    """Test schema creation and basic operations."""

    print("="*70)
    print("STEP 2: Neo4j Schema Setup & Client Test")
    print("="*70 + "\n")

    # Initialize client
    with Neo4jClient(URI, USER, PASSWORD) as client:

        # 1. Setup schema
        client.setup_schema()

        # 2. Create test proposition
        print("📝 Creating test proposition...")

        test_prop = client.create_proposition(
            content="This is a test proposition for schema validation",
            embedding=[0.1] * 1536,  # Dummy embedding
            type="fact",
            certainty="high",
            concepts=["testing", "schema", "validation"],
            source_message_id="test_msg_001",
            source_semantic_unit_id="test_unit_001",
            speaker="user",
            timestamp="2025-10-04T10:00:00Z"
        )

        print(f"✅ Created proposition: {test_prop['id']}")
        print(f"   Content: {test_prop['content']}")
        print(f"   Type: {test_prop['type']}")
        print(f"   Concepts: {test_prop['concepts']}\n")

        # 3. Retrieve it
        print("🔍 Retrieving proposition...")
        retrieved = client.get_proposition(test_prop['id'])
        print(f"✅ Retrieved: {retrieved['content'][:50]}...\n")

        # 4. Create another proposition for edge testing
        print("📝 Creating second proposition...")
        test_prop2 = client.create_proposition(
            content="Second test proposition for edge creation",
            embedding=[0.2] * 1536,
            type="fact",
            certainty="high",
            concepts=["testing", "edges"],
            source_message_id="test_msg_002",
            source_semantic_unit_id="test_unit_002",
            speaker="assistant",
            timestamp="2025-10-04T10:01:00Z"
        )
        print(f"✅ Created: {test_prop2['id']}\n")

        # 5. Create temporal edge
        print("🔗 Creating NEXT edge (temporal)...")
        client.create_temporal_edge(test_prop['id'], test_prop2['id'])
        print("✅ Temporal edge created\n")

        # 6. Create semantic edge
        print("🔗 Creating COHERENT edge (semantic)...")
        client.create_semantic_edge(
            test_prop['id'],
            test_prop2['id'],
            weight=0.85
        )
        print("✅ Semantic edge created\n")

        # 7. Count everything
        print("📊 Database Statistics:")
        prop_count = client.count_propositions()
        edge_counts = client.count_edges()

        print(f"   Propositions: {prop_count}")
        for edge_type, count in edge_counts.items():
            print(f"   {edge_type} edges: {count}")
        print()

        # 8. Get temporal chain
        print("⛓️  Temporal Chain:")
        chain = client.get_temporal_chain()
        if chain:
            print(f"   Length: {chain.get('chain_length', 0)} propositions")
            print(f"   First: {chain.get('first_content', '')[:50]}...")
            print(f"   Last: {chain.get('last_content', '')[:50]}...")
        print()

        # 9. Get semantic neighbors
        print("🔍 Semantic Neighbors:")
        neighbors = client.get_semantic_neighbors(test_prop['id'], min_weight=0.5)
        for neighbor in neighbors:
            print(f"   - {neighbor['content'][:40]}... (similarity: {neighbor['similarity']:.2f})")
        print()

        # 10. Update metadata
        print("📝 Updating proposition metadata...")
        client.update_proposition(
            test_prop['id'],
            activation_count=5,
            coherence_score=0.75
        )
        updated = client.get_proposition(test_prop['id'])
        print(f"✅ Updated: activation_count={updated['activation_count']}, coherence_score={updated['coherence_score']}\n")

        print("="*70)
        print("✅ STEP 2 COMPLETE: Schema & Client Working!")
        print("="*70)
        print("\nReady for STEP 3: Embeddings Integration")

if __name__ == "__main__":
    test_schema()
