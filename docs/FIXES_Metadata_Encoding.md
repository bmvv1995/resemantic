# Metadata Encoding Fixes - Oct 7, 2025

**Issue:** Double JSON encoding causing metadata to be stored as string instead of dict
**Analysis:** Claude Desktop identified critical flow issues
**Status:** ✅ FIXED

---

## Problems Identified

### 1. Double JSON Encoding in Prompts

**Location:** `graphs/extraction_graph.py` lines 242, 301

**Problem:**
```python
# ❌ WRONG (before):
"block_metadata": {json.dumps(su.get('block_metadata', {}), ensure_ascii=False)}
```

**Flow:**
```
1. SU extraction: {"resource_url": "https://..."} (dict)
2. Propositionalize prompt: json.dumps() → '{"resource_url": "https://..."}' (string in prompt!)
3. LLM sees: "block_metadata": "{\"resource_url\": ...}" (escaped string)
4. LLM returns: string value
5. json.loads(): "block_metadata" = STRING, not dict!
```

**Fix:**
```python
# ✅ CORRECT (after):
"block_metadata": {su.get('block_metadata', {})}
```

**Flow fixed:**
```
1. SU extraction: dict
2. Propositionalize prompt: dict (NO encoding!)
3. LLM sees proper dict structure
4. LLM returns: dict value
5. json.loads(): "block_metadata" = dict ✓
```

---

### 2. Neo4j Storage Limitation

**Location:** `storage/neo4j_client.py` line 195

**Problem:** Neo4j properties CANNOT be nested maps

**Technical constraint:**
```python
# Neo4j doesn't support:
CREATE (p {block_metadata: {resource_url: "...", resource_type: "docs"}})
# → Error: Map{} invalid property type
```

**Solution:** Store as JSON string (acceptable trade-off)
```python
"block_metadata": json.dumps(block_metadata) if block_metadata else "{}"
```

**Correct flow:**
```
1. Pipeline: dict → dict → dict (NO encoding until storage!)
2. Storage layer (Neo4j): dict → json.dumps() → string
3. Retrieval: string → json.loads() → dict
```

---

## Query Impact

**Current (JSON string in Neo4j):**
```cypher
// ❌ Direct field access doesn't work:
MATCH (p:Proposition)
WHERE p.block_metadata.resource_url = "https://..."
// Error: block_metadata is string, not map!

// ✅ Must use CONTAINS (slower):
MATCH (p:Proposition)
WHERE p.block_metadata CONTAINS '"resource_url":"https://..."'
RETURN p
```

**Future optimization (FAZA 2):**
- Option A: Flatten key fields (resource_url as top-level property)
- Option B: Separate Block nodes with relationships
- Option C: Hybrid (frequently-queried fields flattened, rest as JSON)

---

## Validation Added

**Location:** `storage/neo4j_client.py` line 167

```python
# Validate block_metadata is dict, not string (catch double encoding)
if block_metadata and isinstance(block_metadata, str):
    raise ValueError(f"block_metadata must be dict at storage layer, got string")
```

**Purpose:** Fail fast if double encoding happens in pipeline

---

## Testing

**Test file:** `test_metadata_fix.py`

**Checks:**
1. Props in Neo4j have block_metadata as string (expected)
2. String parses to dict via json.loads() (valid JSON)
3. Decision blocks have WHY field populated
4. No double encoding artifacts (escaped quotes, etc.)

---

## Summary

| Aspect | Before Fix | After Fix |
|--------|------------|-----------|
| **Prompt encoding** | json.dumps() in prompt | dict direct |
| **Pipeline flow** | dict → string → string | dict → dict → dict |
| **Neo4j storage** | string (correct) | string (correct, documented) |
| **Query efficiency** | CONTAINS (slow) | CONTAINS (slow, FAZA 2 will optimize) |
| **Validation** | None | Fail-fast on type errors |

---

## Credits

**Analysis:** Claude Desktop (Oct 7, 2025)
**Implementation:** Claude Code + User validation
**Testing:** LangSmith + Neo4j direct inspection

---

## Next Steps (FAZA 2)

1. Flatten frequently-queried fields (resource_url, decision_choice)
2. Create indexes on flattened fields
3. Benchmark CONTAINS vs direct field access
4. Decision: Keep hybrid or migrate to separate Block nodes
