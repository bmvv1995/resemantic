"""
SQLite Archive Database for Living Knowledge Ecosystem

Stores raw conversation data and extraction outputs for:
- Traceability (what was the original message?)
- Debugging (QA on extraction quality)
- Audit trail (complete conversation history)

Neo4j = Active graph (retrieval, sleep cycles)
SQLite = Archival storage (raw data, Stage 1/2 outputs)
"""

import sqlite3
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path


class ArchiveDB:
    """SQLite database for archival storage."""

    def __init__(self, db_path: str = "data/resemantic_archive.db"):
        """
        Initialize SQLite archive database.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dict-like access
        self.setup_schema()

    def setup_schema(self):
        """Create tables if they don't exist."""

        cursor = self.conn.cursor()

        # Messages table (raw conversation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Semantic Units table (Stage 1 outputs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_units (
                unit_id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT,
                narrative_role TEXT,
                concepts TEXT,
                entities TEXT,
                decisions TEXT,
                certainty TEXT,
                context_dependencies TEXT,
                impact TEXT,
                relevance TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)

        # Propositions Archive table (Stage 2 outputs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS propositions_archive (
                proposition_id TEXT PRIMARY KEY,
                semantic_unit_id TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT,
                certainty TEXT,
                concepts TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (semantic_unit_id) REFERENCES semantic_units(unit_id)
            )
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp
            ON messages(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_units_message
            ON semantic_units(message_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_propositions_semantic_unit
            ON propositions_archive(semantic_unit_id)
        """)

        self.conn.commit()

    # =========================================================================
    # MESSAGES
    # =========================================================================

    def store_message(
        self,
        message_id: str,
        role: str,
        content: str,
        timestamp: str
    ):
        """
        Store raw message.

        Args:
            message_id: Unique message ID
            role: "user" or "assistant"
            content: Raw message text
            timestamp: ISO timestamp
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO messages (id, role, content, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, role, content, timestamp, datetime.now().isoformat()))
        self.conn.commit()

    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get message by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_messages(self, limit: int = 100) -> List[Dict]:
        """Get all messages ordered by timestamp."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM messages
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # SEMANTIC UNITS
    # =========================================================================

    def store_semantic_unit(
        self,
        unit_id: str,
        message_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Store semantic unit (Stage 1 output).

        Args:
            unit_id: Unique unit ID
            message_id: Parent message ID
            content: Semantic unit content
            metadata: All Stage 1 metadata (type, concepts, etc.)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO semantic_units (
                unit_id, message_id, content, type, narrative_role,
                concepts, entities, decisions, certainty, context_dependencies,
                impact, relevance, metadata, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unit_id,
            message_id,
            content,
            metadata.get('type'),
            metadata.get('narrative_role'),
            json.dumps(metadata.get('concepts', [])),
            json.dumps(metadata.get('entities', [])),
            json.dumps(metadata.get('decisions', [])),
            metadata.get('certainty'),
            json.dumps(metadata.get('context_dependencies', [])),
            metadata.get('impact'),
            metadata.get('relevance'),
            json.dumps(metadata),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def get_semantic_unit(self, unit_id: str) -> Optional[Dict]:
        """Get semantic unit by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM semantic_units WHERE unit_id = ?", (unit_id,))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            # Parse JSON fields
            result['concepts'] = json.loads(result['concepts']) if result['concepts'] else []
            result['entities'] = json.loads(result['entities']) if result['entities'] else []
            result['decisions'] = json.loads(result['decisions']) if result['decisions'] else []
            result['context_dependencies'] = json.loads(result['context_dependencies']) if result['context_dependencies'] else []
            result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
            return result
        return None

    def get_semantic_units_by_message(self, message_id: str) -> List[Dict]:
        """Get all semantic units for a message."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM semantic_units
            WHERE message_id = ?
            ORDER BY created_at
        """, (message_id,))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result['concepts'] = json.loads(result['concepts']) if result['concepts'] else []
            result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
            results.append(result)
        return results

    # =========================================================================
    # PROPOSITIONS ARCHIVE
    # =========================================================================

    def store_proposition(
        self,
        proposition_id: str,
        semantic_unit_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Store proposition (Stage 2 output).

        Args:
            proposition_id: Unique proposition ID (same as Neo4j)
            semantic_unit_id: Parent semantic unit ID
            content: Proposition text
            metadata: All Stage 2 metadata (type, concepts, etc.)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO propositions_archive (
                proposition_id, semantic_unit_id, content,
                type, certainty, concepts, metadata, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposition_id,
            semantic_unit_id,
            content,
            metadata.get('type'),
            metadata.get('certainty'),
            json.dumps(metadata.get('concepts', [])),
            json.dumps(metadata),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def get_proposition(self, proposition_id: str) -> Optional[Dict]:
        """Get proposition by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM propositions_archive
            WHERE proposition_id = ?
        """, (proposition_id,))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            result['concepts'] = json.loads(result['concepts']) if result['concepts'] else []
            result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
            return result
        return None

    # =========================================================================
    # TRACEABILITY QUERIES
    # =========================================================================

    def get_full_lineage(self, proposition_id: str) -> Optional[Dict]:
        """
        Get complete lineage: Message → SemanticUnit → Proposition.

        Args:
            proposition_id: Proposition ID

        Returns:
            {
                "message": {...},
                "semantic_unit": {...},
                "proposition": {...}
            }
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                m.id AS message_id,
                m.role AS message_role,
                m.content AS message_content,
                m.timestamp AS message_timestamp,
                su.unit_id AS semantic_unit_id,
                su.content AS semantic_unit_content,
                su.type AS semantic_unit_type,
                su.narrative_role AS semantic_unit_narrative_role,
                pa.proposition_id AS proposition_id,
                pa.content AS proposition_content,
                pa.type AS proposition_type
            FROM propositions_archive pa
            JOIN semantic_units su ON pa.semantic_unit_id = su.unit_id
            JOIN messages m ON su.message_id = m.id
            WHERE pa.proposition_id = ?
        """, (proposition_id,))

        row = cursor.fetchone()
        if row:
            return {
                "message": {
                    "id": row['message_id'],
                    "role": row['message_role'],
                    "content": row['message_content'],
                    "timestamp": row['message_timestamp']
                },
                "semantic_unit": {
                    "unit_id": row['semantic_unit_id'],
                    "content": row['semantic_unit_content'],
                    "type": row['semantic_unit_type'],
                    "narrative_role": row['semantic_unit_narrative_role']
                },
                "proposition": {
                    "proposition_id": row['proposition_id'],
                    "content": row['proposition_content'],
                    "type": row['proposition_type']
                }
            }
        return None

    # =========================================================================
    # STATS
    # =========================================================================

    def get_stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM semantic_units")
        semantic_unit_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM propositions_archive")
        proposition_count = cursor.fetchone()[0]

        return {
            "messages": message_count,
            "semantic_units": semantic_unit_count,
            "propositions": proposition_count
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
