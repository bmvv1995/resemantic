"""
Test Neo4j connection with different credential variants
"""
from neo4j import GraphDatabase

URI = "bolt://172.105.85.181:7687"

# Try different credential combinations
credentials = [
    ("neo4j", "password123"),
    ("neo4j", "neo4j"),  # Default
    ("neo4j", ""),
    ("admin", "password123"),
]

for user, password in credentials:
    print(f"\n🔐 Testing: user='{user}', password='{password}'")

    try:
        driver = GraphDatabase.driver(URI, auth=(user, password))
        driver.verify_connectivity()
        print(f"   ✅ SUCCESS with user='{user}', password='{password}'")

        # Test query
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
            print(f"   ✅ Query test passed")

        driver.close()
        break

    except Exception as e:
        error_msg = str(e)
        if "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower():
            print(f"   ❌ Auth failed")
        else:
            print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("ℹ️  If all failed, possible issues:")
print("   1. Password needs to be reset via Neo4j Browser")
print("   2. Different auth method required")
print("   3. Network/firewall blocking connection")
