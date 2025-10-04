"""
Test SQLite Archive Database
"""
from storage.archive_db import ArchiveDB

def test_archive():
    """Test archive database operations."""

    print("="*70)
    print("SQLite Archive Database Test")
    print("="*70 + "\n")

    with ArchiveDB() as archive:

        # 1. Store message
        print("📝 Storing test message...")
        archive.store_message(
            message_id="msg_001",
            role="user",
            content="buna. ce inseamna pentru tine o unitate semantica?",
            timestamp="2025-10-04T10:00:00Z"
        )
        print("✅ Message stored\n")

        # 2. Retrieve message
        print("🔍 Retrieving message...")
        msg = archive.get_message("msg_001")
        print(f"✅ Retrieved: {msg['content'][:50]}...\n")

        # 3. Store semantic unit
        print("📝 Storing semantic unit...")
        archive.store_semantic_unit(
            unit_id="unit_001",
            message_id="msg_001",
            content="User-ul salută și întreabă ce înseamnă o unitate semantică",
            metadata={
                "type": "question",
                "narrative_role": "core",
                "concepts": ["unitate semantică", "definiție"],
                "certainty": "high",
                "impact": "major"
            }
        )
        print("✅ Semantic unit stored\n")

        # 4. Retrieve semantic unit
        print("🔍 Retrieving semantic unit...")
        unit = archive.get_semantic_unit("unit_001")
        print(f"✅ Retrieved: {unit['content']}")
        print(f"   Type: {unit['type']}")
        print(f"   Concepts: {unit['concepts']}\n")

        # 5. Store propositions
        print("📝 Storing propositions...")
        archive.store_proposition(
            proposition_id="prop_001",
            semantic_unit_id="unit_001",
            content="User salută",
            metadata={
                "type": "fact",
                "certainty": "high",
                "concepts": ["salut"]
            }
        )
        archive.store_proposition(
            proposition_id="prop_002",
            semantic_unit_id="unit_001",
            content="User întreabă ce înseamnă o unitate semantică",
            metadata={
                "type": "question",
                "certainty": "high",
                "concepts": ["unitate semantică", "definiție"]
            }
        )
        print("✅ 2 propositions stored\n")

        # 6. Get full lineage
        print("🔗 Getting full lineage (Message → SemanticUnit → Proposition)...")
        lineage = archive.get_full_lineage("prop_002")
        print(f"\n📨 Original Message:")
        print(f"   {lineage['message']['content']}")
        print(f"\n📝 Semantic Unit:")
        print(f"   {lineage['semantic_unit']['content']}")
        print(f"\n⚛️  Proposition:")
        print(f"   {lineage['proposition']['content']}\n")

        # 7. Stats
        print("📊 Database Statistics:")
        stats = archive.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()

        print("="*70)
        print("✅ SQLite Archive Database Working!")
        print("="*70)
        print(f"\n📁 Database file: {archive.db_path}")
        print("\n🎯 Ready for integration with extraction pipeline")

if __name__ == "__main__":
    test_archive()
