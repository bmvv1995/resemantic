"""
Test Neo4j connection
"""
from neo4j import GraphDatabase
import sys

# Connection details
URI = "bolt://172.105.85.181:7687"  # Bolt protocol port
USER = "neo4j"
PASSWORD = "password123"

def test_connection():
    """Test basic Neo4j connection."""

    print("🔗 Attempting to connect to Neo4j...")
    print(f"   URI: {URI}")
    print(f"   User: {USER}")

    try:
        # Create driver
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

        # Verify connectivity
        driver.verify_connectivity()

        print("✅ Connection successful!\n")

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
            print(f"📈 Existing nodes in database: {count}")

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            rel_count = result.single()['rel_count']
            print(f"📈 Existing relationships: {rel_count}\n")

        driver.close()
        print("✅ Connection test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\n🔍 Troubleshooting:")
        print(f"   - Check if Neo4j is running at {URI}")
        print(f"   - Verify credentials (user: {USER})")
        print(f"   - Check firewall/network access")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
