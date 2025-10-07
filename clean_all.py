#!/usr/bin/env python3
"""
Clean ALL storage - Neo4j + SQLite
Fresh start for ReSemantic
"""
import os
from neo4j import GraphDatabase

# Neo4j config
NEO4J_URI = "bolt://172.105.85.181:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "test1234"

# SQLite databases
SQLITE_DBS = [
    "./data/resemantic_archive.db",
    "./langgraph_studio/data/resemantic_archive.db"
]

def clean_neo4j():
    """Delete all nodes and relationships from Neo4j."""
    print("\n🧹 Cleaning Neo4j database...")
    print("="*60)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Check before
            result = session.run("MATCH (n) RETURN count(n) AS count")
            before_nodes = result.single()['count']
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            before_rels = result.single()['count']
            
            print(f"📊 Before: {before_nodes} nodes, {before_rels} relationships")
            
            if before_nodes == 0:
                print("✅ Neo4j already empty")
            else:
                # Delete all
                session.run("MATCH ()-[r]->() DELETE r")
                session.run("MATCH (n) DELETE n")
                
                # Verify
                result = session.run("MATCH (n) RETURN count(n) AS count")
                after_nodes = result.single()['count']
                
                print(f"✅ Deleted: {before_nodes} nodes, {before_rels} relationships")
                
                if after_nodes == 0:
                    print("✅ Neo4j successfully cleaned!")
                else:
                    print(f"⚠️  Warning: {after_nodes} nodes remain")
    
    finally:
        driver.close()

def clean_sqlite():
    """Delete SQLite database files."""
    print("\n🧹 Cleaning SQLite databases...")
    print("="*60)
    
    deleted = 0
    for db_path in SQLITE_DBS:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"✅ Deleted: {db_path}")
                deleted += 1
            except Exception as e:
                print(f"❌ Error deleting {db_path}: {e}")
        else:
            print(f"⚪ Not found: {db_path}")
    
    if deleted > 0:
        print(f"✅ Deleted {deleted} SQLite database(s)")
    else:
        print("✅ No SQLite databases to delete")

def main():
    """Clean everything."""
    print("\n" + "="*60)
    print("🗑️  CLEAN ALL - Neo4j + SQLite")
    print("="*60)
    
    # Confirm
    response = input("\n⚠️  This will DELETE ALL data! Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Cancelled")
        return
    
    # Clean
    clean_neo4j()
    clean_sqlite()
    
    print("\n" + "="*60)
    print("🆕 FRESH START - All storage cleaned!")
    print("="*60)
    print("\n💡 Tip: Run chat_cli_batch.py to start new conversation\n")

if __name__ == "__main__":
    main()
