"""
Test Neo4j connection - all variants
"""
from neo4j import GraphDatabase

# Try both URIs and multiple passwords
test_configs = [
    ("bolt://172.105.85.181:7687", "neo4j", "password123"),
    ("bolt://localhost:7687", "neo4j", "password123"),
    ("bolt://127.0.0.1:7687", "neo4j", "password123"),
    ("bolt://172.105.85.181:7687", "neo4j", "neo4j"),
    ("bolt://172.105.85.181:7687", "neo4j", "admin"),
    ("bolt://172.105.85.181:7687", "neo4j", ""),
]

print("Testing all connection variants...\n")
print("=" * 70)

for uri, user, password in test_configs:
    print(f"\n🔐 Testing:")
    print(f"   URI: {uri}")
    print(f"   User: {user}")
    print(f"   Password: {'(empty)' if not password else password}")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()

        print(f"   ✅ ✅ ✅ SUCCESS! ✅ ✅ ✅")

        # Test actual query
        with driver.session() as session:
            result = session.run("RETURN 'Connection works!' AS msg")
            msg = result.single()['msg']
            print(f"   📨 Query result: {msg}")

            # Get node count
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()['count']
            print(f"   📊 Nodes in DB: {count}")

        driver.close()

        print(f"\n{'=' * 70}")
        print(f"✅ WORKING CREDENTIALS FOUND:")
        print(f"   URI: {uri}")
        print(f"   User: {user}")
        print(f"   Password: {password}")
        print(f"{'=' * 70}")
        break

    except Exception as e:
        error_str = str(e)
        if "unauthorized" in error_str.lower() or "authentication" in error_str.lower():
            print(f"   ❌ Auth failed")
        elif "connection" in error_str.lower() or "refused" in error_str.lower():
            print(f"   ❌ Connection refused (server not reachable at this URI)")
        else:
            print(f"   ❌ Error: {error_str[:100]}")

print("\n" + "=" * 70)
print("\nℹ️  If all failed:")
print("   1. Check password in Neo4j Browser")
print("   2. Try running in Browser: ALTER USER neo4j SET PASSWORD 'test123'")
print("   3. Confirm you can connect in Browser with same credentials")
