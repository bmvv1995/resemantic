"""
Test Neo4j connection with updated password
"""
from neo4j import GraphDatabase
import sys

URI = "bolt://172.105.85.181:7687"
USER = "neo4j"
PASSWORD = "test1234"

def test_connection():
    """Test basic Neo4j connection."""

    print("🔗 Attempting to connect to Neo4j...")
    print(f"   URI: {URI}")
    print(f"   User: {USER}")
    print(f"   Password: {PASSWORD}")

    try:
        # Create driver
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

        # Verify connectivity
        driver.verify_connectivity()

        print("\n✅ ✅ ✅ CONNECTION SUCCESSFUL! ✅ ✅ ✅\n")

        # Test query
        with driver.session() as session:
            result = session.run("RETURN 'Hello from Neo4j!' AS message")
            record = result.single()
            print(f"📨 Test query result: {record['message']}\n")

            # Get database info
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            for record in result:
                print(f"📊 Neo4j Info:")
                print(f"   Name: {record['name']}")
                print(f"   Version: {record['versions'][0]}")
                print(f"   Edition: {record['edition']}\n")

        # Check existing data
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            count = result.single()['node_count']
            print(f"📈 Current database status:")
            print(f"   Nodes: {count}")

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            rel_count = result.single()['rel_count']
            print(f"   Relationships: {rel_count}\n")

        driver.close()

        print("=" * 70)
        print("✅ STEP 1 COMPLETE: Neo4j Connection Verified")
        print("=" * 70)
        print("\nWorking credentials:")
        print(f"  URI: {URI}")
        print(f"  User: {USER}")
        print(f"  Password: {PASSWORD}")
        print("\nReady to proceed to STEP 2: Schema Creation")

        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
