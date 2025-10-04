"""
Validate Neo4j graph structure after processing
"""
from storage import Neo4jClient

neo4j = Neo4jClient(
    uri="bolt://172.105.85.181:7687",
    user="neo4j",
    password="test1234"
)

print("="*70)
print("NEO4J GRAPH VALIDATION")
print("="*70 + "\n")

# Count nodes and edges
with neo4j.driver.session() as session:
    # Get all propositions
    result = session.run("""
        MATCH (p:Proposition)
        RETURN p.id as id, p.content as content, p.speaker as speaker,
               p.type as type, p.certainty as certainty,
               size(p.embedding) as embedding_dim
        ORDER BY p.timestamp
    """)

    props = list(result)

    print(f"📊 PROPOSITIONS: {len(props)}\n")

    for i, prop in enumerate(props, 1):
        print(f"{i}. [{prop['speaker']}] {prop['type']} ({prop['certainty']})")
        print(f"   {prop['content'][:80]}...")
        print(f"   Embedding: {prop['embedding_dim']} dimensions")
        print(f"   ID: {prop['id'][:8]}...\n")

    # Check NEXT edges
    result = session.run("""
        MATCH (p1:Proposition)-[r:NEXT]->(p2:Proposition)
        RETURN count(r) as count
    """)
    next_count = result.single()['count']

    print(f"\n⏭️  NEXT EDGES: {next_count}")

    # Sample NEXT edges
    result = session.run("""
        MATCH (p1:Proposition)-[r:NEXT]->(p2:Proposition)
        RETURN p1.content as from_content, p2.content as to_content
        LIMIT 3
    """)

    print("\nSample temporal flow:")
    for rec in result:
        print(f"   {rec['from_content'][:50]}...")
        print(f"   ↓")
        print(f"   {rec['to_content'][:50]}...\n")

    # Check COHERENT edges
    result = session.run("""
        MATCH (p1:Proposition)-[r:COHERENT]->(p2:Proposition)
        RETURN count(r) as count,
               min(r.weight) as min_sim,
               max(r.weight) as max_sim,
               avg(r.weight) as avg_sim
    """)

    coherent = result.single()
    print(f"\n🔗 COHERENT EDGES: {coherent['count']}")
    print(f"   Similarity range: {coherent['min_sim']:.3f} - {coherent['max_sim']:.3f}")
    print(f"   Average similarity: {coherent['avg_sim']:.3f}")

    # Sample high-similarity edges
    result = session.run("""
        MATCH (p1:Proposition)-[r:COHERENT]->(p2:Proposition)
        WHERE r.weight > 0.5
        RETURN p1.content as from_content, p2.content as to_content, r.weight as similarity
        ORDER BY r.weight DESC
        LIMIT 5
    """)

    print("\nTop semantic connections (similarity > 0.5):")
    for rec in result:
        print(f"\n   Similarity: {rec['similarity']:.3f}")
        print(f"   {rec['from_content'][:60]}...")
        print(f"   ↔")
        print(f"   {rec['to_content'][:60]}...")

    # Check vector index
    result = session.run("SHOW INDEXES")
    indexes = list(result)

    print(f"\n\n📇 INDEXES: {len(indexes)}")
    for idx in indexes:
        print(f"   {idx['name']}: {idx['type']}")

print("\n" + "="*70)
print("✅ VALIDATION COMPLETE")
print("="*70)

neo4j.close()
