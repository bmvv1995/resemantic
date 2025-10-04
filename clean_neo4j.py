"""
Clean Neo4j database - delete all nodes and relationships
"""
from neo4j import GraphDatabase

URI = "bolt://172.105.85.181:7687"
USER = "neo4j"
PASSWORD = "test1234"

def clean_database():
    """Delete all nodes and relationships."""

    print("🧹 Cleaning Neo4j database...\n")

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    try:
        with driver.session() as session:
            # Check what exists before cleaning
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            before_nodes = result.single()['node_count']

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            before_rels = result.single()['rel_count']

            print(f"📊 Current state:")
            print(f"   Nodes: {before_nodes}")
            print(f"   Relationships: {before_rels}\n")

            if before_nodes == 0 and before_rels == 0:
                print("✅ Database already empty!\n")
                return

            # Delete all relationships first
            print("🗑️  Deleting all relationships...")
            session.run("MATCH ()-[r]->() DELETE r")

            # Delete all nodes
            print("🗑️  Deleting all nodes...")
            session.run("MATCH (n) DELETE n")

            # Verify clean
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            after_nodes = result.single()['node_count']

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count")
            after_rels = result.single()['rel_count']

            print(f"\n📊 After cleaning:")
            print(f"   Nodes: {after_nodes}")
            print(f"   Relationships: {after_rels}\n")

            if after_nodes == 0 and after_rels == 0:
                print("✅ Database successfully cleaned!")
                print("🆕 Ready for fresh start!\n")
            else:
                print("⚠️  Warning: Some data remains")

    finally:
        driver.close()

if __name__ == "__main__":
    clean_database()
