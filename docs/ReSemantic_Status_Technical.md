# ReSemantic: Memory Architecture for Conversational AI
**Current Status & Technical Approach**

*Document pentru evaluare tehnică - Octombrie 2025*

---

## Context

Conversațiile cu LLM-uri au o problemă fundamentală: contextul se pierde. Nu pentru că modelele nu pot reține - ci pentru că **nu există o arhitectură de memorie semantică persistentă**.

Rezultatul: users repetă același context, AI-ul "uită" decizii anterioare, knowledge-ul valoros din conversații dispare.

ReSemantic abordează asta diferit: tratează conversațiile ca **streams semantice** care trebuie descompuse, indexate și făcute traversabile.

---

## Premisele Arhitecturale

### 1. "Agenda" - Blocks ca Sistem de Acces Rapid

**Observație:** Când cauți ceva în memorie, nu vrei să citești totul. Vrei **categorii rapide** - ca în agenda fizică:
- "Unde era linkul API?" → Secțiunea Resources
- "De ce am ales X?" → Secțiunea Decisions (cu WHY explicit)
- "Unde e fișierul config?" → Secțiunea Documents

**Implementare:** Metadata blocks extrase automat și **duplicate în fiecare proposition**:
```
Proposition node:
├─ content (pentru embedding similarity)
├─ embedding (vector search)
├─ block_metadata (JSON string):
    ├─ resource_url (dacă relevant)
    ├─ decision_choice + decision_reason (WHY!) 
    └─ doc_location (dacă relevant)
```

**Trade-off acceptat:** Redundanță (metadata duplicată) pentru **zero joins la retrieval**. Query = un singur hop.

### 2. Memorie Traversabilă - Graph ca Substrate

**Decizie:** Neo4j, nu vector DB clasic.

**Motivație:** Embedding similarity e doar **entry point**. Contextul real vine din:
- **COHERENT edges** - semantic similarity între propositions (>0.7 cosine)
- **NEXT edges** - temporal flow (conversație ca lanț)

**Pattern actual:**
1. Vector search → găsește 3-5 entry points (propositions relevante)
2. Graph traversal → expand prin COHERENT edges (1-2 hops)
3. Context assembly → reconstituie semantic unit, apoi mesaj complet

Rezultat: **retrieval nu e search, e explorare**. Contextul se "desfășoară" natural prin graf.

### 3. Sleep Cycles - Consolidare & Uitare Selectivă

**Încă în design, dar premisele sunt clare:**

**Observație biologică:** Creierul uman nu reține totul egal:
- Sleep consolidează ce e important (reactivări repetate)
- Uitarea e **activă** (synaptic pruning), nu pasivă

**Analog pentru graf:**

**Consolidare:**
- Propositions accesate des → `activation_count++`
- Threshold trigger → upgrade la "long-term" (persistent cu prioritate)
- Clustering semantic → grup propositions corelate (compound memories)

**Uitare selectivă:**
- Propositions cu `activation_count` = 0 după N zile → candidat weakening
- `is_weak = true` + `weakness_reason` (low activation, redundant)
- Eventual cleanup: edge removal, apoi node removal (gradual)

**Critical:** Uitarea nu e delete brutal. E:
1. Detect weak signals (usage patterns)
2. Mark & monitor (poate devine relevant)
3. Progressive fade (edges → metadata → eventual node)

**Trade-off:** Păstrezi tot = poluare & retrieval noise. Uiți agresiv = pierzi context subtil. Echilibrul e în **metrics** (ce măsori pentru "important").

---

## Current State - What Works

### Extraction Pipeline (2-Stage)

**Stage 1 - Semantic Units cu Blocks:**
- LLM reformulează mesajul cu context (rezolvă "da" → "user confirmă X")
- Detectează type (decision/resource/document/question/etc)
- Extrage blocks relevant pentru type:
  - Resource: URL + type + discussed_context
  - Decision: choice + **WHY** (explicit reasoning) + alternatives + confidence
  - Document: filename + location + purpose

**Stage 2 - Propositionalization:**
- Descompune semantic unit în atomic propositions (1-6 per mesaj)
- Metadata blocks **duplicate automat** în fiecare proposition
- Concepts extraction (specific terms, compound: "webhook_retry_mechanism")

**Timing:** ~15s per conversation turn (user + assistant batch)
- Calitate prioritară (zero compromis pe WHY capture sau blocks)
- Redundanță eliminată recent (era 25-30s)

### Storage - Dual System

**Neo4j (graph):**
- Propositions ca nodes (cu embedding + block_metadata JSON)
- COHERENT edges (cosine >0.7, bidirectional)
- NEXT edges (temporal flow, unidirectional)
- Vector index nativ (embedding similarity search)

**SQLite (archive):**
- Raw messages (immutable)
- Semantic units (cu metadata complet)
- Propositions (backup cu all fields)
- Source of truth pentru rebuild

### Retrieval - Hybrid

**Actual (funcțional):**
1. Embedding similarity → top K propositions
2. Filter by block type (dacă relevant query)
3. Return cu context complet (metadata inline)

**În lucru:**
- Graph traversal expand (1-2 hop COHERENT)
- Temporal context injection (NEXT edges pentru story)

---

## Design Decisions & Rationale

### De ce duplicate metadata în props?

**Alternativa:** Metadata doar în semantic units, props linkuiesc.

**Problema:** Retrieval = 2 queries (prop → SU → metadata). Latency + complexity.

**Soluție actuală:** Duplicate în props ca JSON string.
- Write: once per extraction
- Read: many times (retrieval constant)
- Trade-off: storage space vs **retrieval speed** (zero compromise aici)

### De ce JSON string pentru block_metadata în Neo4j?

Neo4j nu acceptă nested objects ca properties (type error: Map{} invalid).

**Soluție:** `json.dumps()` la write, `json.loads()` la read.
- Compromis acceptabil: 1 parse operation vs impossibility
- Alternativa (flatten toate fields) = poluare property space + loss of structure

### De ce blocks în prompt, nu post-process?

**Încercat:** Lăsăm LLM să extragă semantic units, apoi regex/parser pentru blocks.

**Eșec:** Parsing fragil (URL-uri în diverse formate, decizii implicite vs explicite).

**Concluzie:** LLM-ul e **cel mai bun block extractor**. Prompt engineering > post-processing.

---

## Open Questions & Next Steps

### 1. Sleep Cycles Implementation

**Întrebare:** Ce metrics pentru "important"?
- Activation count alone? (risc: popular ≠ important)
- Semantic centrality? (PageRank-style în COHERENT graph)
- User feedback signals? (thumbs up/down pe retrieval)

**Explorare necesară:** Hybrid scoring (usage + structure + feedback).

### 2. Retrieval Strategy Refinement

**Actual:** Embedding similarity cu block filtering.

**Posibil:** 
- Graph traversal cu bounded cost (max 2 hops, threshold decay)
- Temporal boost (recent > old pentru same similarity)
- Concept clustering (grup props cu overlapping concepts pentru compound answers)

**Trade-off:** Complexity vs quality. Când oprești traversal-ul?

### 3. Blocks Evolution

**Current:** 3 core blocks (resource, decision, document).

**Viitor:**
- Optional blocks (credentials - references only!, contacts, deadlines)
- Community blocks (user-defined schemas, shared templates)
- Versioning (schema evolution fără breaking changes)

**Întrebare:** Cât de extensibil fără a deveni unwieldy?

### 4. Context Window Management

**Challenge:** LLM context limit (200K tokens = multe propositions).

**Strategii posibile:**
- Tiered retrieval (summary level → detail pe request)
- Compression (semantic units ca "super-nodes" pentru overview)
- Selective expansion (doar ramuri relevante din graf)

**Încă nedecis:** Ce expui la nivel de context vs ce ții în graf pentru deep dive.

---

## Implicații Practice

### Pentru Developers

**Good:**
- API simplu (send message → extraction + storage automatic)
- Retrieval transparent (query → context cu blocks inline)
- Extensibil (custom block types posibile)

**Challenging:**
- Tuning retrieval strategy (embedding threshold, hop count, filters)
- Managing graph growth (când cleanup, ce metrics)
- Balancing extraction speed vs quality (prompt optimization trade-offs)

### Pentru Research

**Interesting angles:**
- Sleep cycles ca active forgetting (analog biologic în systems)
- Graph structure emergence (COHERENT edges = semantic topology)
- Blocks ca structured memory primitives (vs flat embeddings)
- Cross-conversation knowledge (same concepts în conversații diferite)

### Pentru Production Use

**Ready:**
- Extraction pipeline stable
- Storage dual-layer functional
- Basic retrieval works

**Needs work:**
- Scalability testing (10K+ conversations)
- Sleep cycles (cleanup strategy)
- Advanced retrieval (graph traversal tuning)
- Monitoring & observability (ce măsori pentru health)

---

## Conclusion - Where We Stand

ReSemantic nu e un vector database cu extra steps. E o **arhitectură de memorie semantică** cu premisele:

1. **Blocks = rapid access categories** (agenda mentală pentru conversații)
2. **Graph = traversable context** (nu doar similarity, ci semantic neighborhood)
3. **Sleep cycles = active curation** (uitare inteligentă, nu acumulare pasivă)

**Current state:** Extraction + storage solid. Retrieval basic functional. Sleep cycles în design.

**Next critical:** Traversal strategy + consolidation/forgetting metrics.

**Open for:** Collaboration pe sleep cycles design, retrieval optimization, scalability testing.

---

*Document pregătit pentru evaluare tehnică. Questions, critiques, și alternative approaches welcome.*

*Contact: vezi README pentru setup & testing.*
