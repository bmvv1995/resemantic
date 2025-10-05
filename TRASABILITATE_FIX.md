# 🔍 Trasabilitate Completă - Plan de Implementare

## Metadata Lipsă (pentru reproducibilitate)

### 1. Extraction Metadata
Adaugă în **Proposition** node (Neo4j):
```python
extraction_metadata = {
    "llm_model": "claude-3-5-haiku-20241022",
    "llm_temperature": 0.3,
    "extraction_version": "v1.0",  # Versioning prompts
    "stage1_prompt_hash": "sha256...",  # Detect prompt changes
    "stage2_prompt_hash": "sha256...",
}
```

### 2. Embedding Metadata
```python
embedding_metadata = {
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "embedding_timestamp": "2025-10-04T20:00:00Z",
    "openai_version": "1.x.x"
}
```

### 3. Edge Provenance
```python
# COHERENT edge properties:
{
    "similarity": 0.87,
    "created_at": "timestamp",
    "algorithm": "cosine",  # sau "euclidean", etc
    "top_k_threshold": 10
}
```

### 4. Audit Trail Extension (SQLite)

```sql
CREATE TABLE extraction_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT,
    config_snapshot TEXT,  -- JSON cu toată config
    llm_model TEXT,
    embedding_model TEXT,
    propositions_created INTEGER,
    edges_created INTEGER,
    duration_seconds REAL
);

CREATE TABLE proposition_lineage (
    proposition_id TEXT,
    run_id TEXT,
    stage1_duration REAL,
    stage2_duration REAL,
    embedding_duration REAL,
    FOREIGN KEY(proposition_id) REFERENCES propositions_archive(proposition_id),
    FOREIGN KEY(run_id) REFERENCES extraction_runs(run_id)
);
```

## Beneficii:
✅ Reproducibility: "Rulează exact aceeași versiune din Aug 2024"
✅ A/B Testing: "Claude Haiku vs Sonnet - care e mai bun?"
✅ Debugging: "De ce proposition X are embedding diferit acum?"
✅ Compliance: "Arată-mi EXACT cum ai generat decizia Y"
