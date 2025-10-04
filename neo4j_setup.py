"""
Neo4j setup for ReSemantic project.
Clean existing data and create new schema for Propositions.
"""

from neo4j import GraphDatabase
import os


class Neo4jSetup:
    """Setup Neo4j database for proposition-based memory."""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clean_database(self):
        """Delete all existing data."""
        with self.driver.session() as session:
            print("🗑️  Deleting all nodes and relationships...")

            # Delete all relationships first
            result = session.run("MATCH ()-[r]->() DELETE r RETURN count(r) as deleted")
            rel_count = result.single()['deleted']
            print(f"   Deleted {rel_count} relationships")

            # Delete all nodes
            result = session.run("MATCH (n) DELETE n RETURN count(n) as deleted")
            node_count = result.single()['deleted']
            print(f"   Deleted {node_count} nodes")

            print("✅ Database cleaned")

    def drop_indexes(self):
        """Drop all existing indexes and constraints."""
        with self.driver.session() as session:
            print("🗑️  Dropping existing indexes and constraints...")

            # Get all indexes
            indexes = session.run("SHOW INDEXES").data()
            for idx in indexes:
                idx_name = idx.get('name')
                if idx_name:
                    try:
                        session.run(f"DROP INDEX {idx_name} IF EXISTS")
                        print(f"   Dropped index: {idx_name}")
                    except Exception as e:
                        print(f"   Could not drop {idx_name}: {e}")

            # Get all constraints
            constraints = session.run("SHOW CONSTRAINTS").data()
            for const in constraints:
                const_name = const.get('name')
                if const_name:
                    try:
                        session.run(f"DROP CONSTRAINT {const_name} IF EXISTS")
                        print(f"   Dropped constraint: {const_name}")
                    except Exception as e:
                        print(f"   Could not drop {const_name}: {e}")

            print("✅ Indexes and constraints dropped")

    def create_schema(self):
        """Create schema for Proposition nodes."""
        with self.driver.session() as session:
            print("🏗️  Creating schema for Propositions...")

            # Create constraint on proposition ID (unique)
            session.run("""
                CREATE CONSTRAINT proposition_id_unique IF NOT EXISTS
                FOR (p:Proposition)
                REQUIRE p.id IS UNIQUE
            """)
            print("   ✅ Created unique constraint on Proposition.id")

            # Create index on source_message_id (for filtering by message)
            session.run("""
                CREATE INDEX proposition_message_idx IF NOT EXISTS
                FOR (p:Proposition)
                ON (p.source_message_id)
            """)
            print("   ✅ Created index on source_message_id")

            # Create index on timestamp (for temporal queries)
            session.run("""
                CREATE INDEX proposition_timestamp_idx IF NOT EXISTS
                FOR (p:Proposition)
                ON (p.timestamp)
            """)
            print("   ✅ Created index on timestamp")

            # Create index on narrative_role (for filtering)
            session.run("""
                CREATE INDEX proposition_narrative_role_idx IF NOT EXISTS
                FOR (p:Proposition)
                ON (p.narrative_role)
            """)
            print("   ✅ Created index on narrative_role")

            # Create index on type (for filtering)
            session.run("""
                CREATE INDEX proposition_type_idx IF NOT EXISTS
                FOR (p:Proposition)
                ON (p.type)
            """)
            print("   ✅ Created index on type")

            # Create full-text index on content (for keyword search)
            session.run("""
                CREATE FULLTEXT INDEX proposition_content_fulltext IF NOT EXISTS
                FOR (p:Proposition)
                ON EACH [p.content]
            """)
            print("   ✅ Created full-text index on content")

            print("✅ Schema created")

    def create_vector_index(self, dimension=1536):
        """Create vector index for embeddings (if Neo4j supports it)."""
        with self.driver.session() as session:
            print(f"🔍 Creating vector index for embeddings (dim={dimension})...")

            try:
                # Try to create vector index (requires Neo4j 5.11+)
                session.run(f"""
                    CREATE VECTOR INDEX proposition_embedding_idx IF NOT EXISTS
                    FOR (p:Proposition)
                    ON p.embedding
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: {dimension},
                            `vector.similarity_function`: 'cosine'
                        }}
                    }}
                """)
                print("   ✅ Created vector index for embeddings")
                return True
            except Exception as e:
                print(f"   ⚠️  Vector index not supported: {e}")
                print(f"   ℹ️  Vector search will work but without index optimization")
                print(f"   ℹ️  (Requires Neo4j 5.11+ Enterprise or AuraDB)")
                return False

    def verify_setup(self):
        """Verify the setup."""
        with self.driver.session() as session:
            print("\n📊 Verifying setup...")

            # Check node count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            print(f"   Nodes: {node_count}")

            # Check relationship count
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"   Relationships: {rel_count}")

            # List indexes
            indexes = session.run("SHOW INDEXES").data()
            print(f"   Indexes: {len(indexes)}")
            for idx in indexes:
                print(f"      - {idx.get('name')}: {idx.get('labelsOrTypes')} on {idx.get('properties')}")

            # List constraints
            constraints = session.run("SHOW CONSTRAINTS").data()
            print(f"   Constraints: {len(constraints)}")
            for const in constraints:
                print(f"      - {const.get('name')}")

            print("\n✅ Setup verified!")

    def create_sample_proposition(self):
        """Create a sample proposition to test schema."""
        with self.driver.session() as session:
            print("\n🧪 Creating sample proposition...")

            session.run("""
                CREATE (p:Proposition {
                    id: 'test_001',
                    content: 'This is a test proposition',
                    embedding: [0.1, 0.2, 0.3],
                    type: 'fact',
                    certainty: 'high',
                    concepts: ['test', 'sample'],
                    source_message_id: 'msg_001',
                    timestamp: datetime(),
                    semantic_unit_content: 'This is the semantic unit that generated this proposition',
                    narrative_role: 'core',
                    relevance: 'high',
                    impact: 'minor',
                    speaker: 'user'
                })
                RETURN p
            """)

            print("   ✅ Sample proposition created")

            # Verify
            result = session.run("MATCH (p:Proposition {id: 'test_001'}) RETURN p")
            prop = result.single()
            if prop:
                print(f"   ✅ Verified: {prop['p']['content']}")

            # Delete sample
            session.run("MATCH (p:Proposition {id: 'test_001'}) DELETE p")
            print("   ✅ Sample deleted")


def main():
    """Main setup script."""

    # Connection details
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "password123"

    print("="*70)
    print("🚀 ReSemantic Neo4j Setup")
    print("="*70)
    print(f"\nConnecting to: {URI}")

    setup = Neo4jSetup(URI, USER, PASSWORD)

    try:
        # Step 1: Clean existing data
        print("\n" + "="*70)
        print("STEP 1: Clean Database")
        print("="*70)
        setup.clean_database()

        # Step 2: Drop indexes
        print("\n" + "="*70)
        print("STEP 2: Drop Indexes")
        print("="*70)
        setup.drop_indexes()

        # Step 3: Create new schema
        print("\n" + "="*70)
        print("STEP 3: Create Schema")
        print("="*70)
        setup.create_schema()

        # Step 4: Create vector index
        print("\n" + "="*70)
        print("STEP 4: Create Vector Index")
        print("="*70)
        setup.create_vector_index(dimension=1536)  # OpenAI text-embedding-3-small

        # Step 5: Verify setup
        print("\n" + "="*70)
        print("STEP 5: Verify Setup")
        print("="*70)
        setup.verify_setup()

        # Step 6: Test with sample
        print("\n" + "="*70)
        print("STEP 6: Test Schema")
        print("="*70)
        setup.create_sample_proposition()

        print("\n" + "="*70)
        print("✅ SETUP COMPLETE!")
        print("="*70)
        print("\nDatabase is ready for ReSemantic propositions!")
        print("\nNext steps:")
        print("1. Process conversations through FIXED pipeline")
        print("2. Generate embeddings for propositions")
        print("3. Insert propositions into Neo4j")
        print("4. Create temporal and semantic links")

    finally:
        setup.close()


if __name__ == "__main__":
    main()
