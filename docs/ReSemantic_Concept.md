# ReSemantic: Pre-Calculated Semantic Topology for Conversations

*The core concept and how it unfolds*

---

## The Central Idea

What if conversation memory wasn't about **storing and searching** - but about building a **traversable semantic topology**?

Think OLAP, but for meaning instead of metrics:
- OLAP pre-aggregates data along dimensions → fast queries without re-computation
- This pre-calculates semantic relationships → fast traversal without re-embedding

**Core concept:** At write time (conversation happens), we pay the cost to extract semantic structure and calculate all relationships. At read time (retrieval), we just navigate the pre-built topology.

Query doesn't compute similarity. Query **walks through pre-existing connections**.

---

## Why This Matters

LLMs lose context when you close the tab. The standard fix: RAG with vector databases.

**Vector DB approach:**
- Store conversation chunks with embeddings
- At query: compute similarity against ALL embeddings
- Return top K matches

Works, but it's **runtime computation every time**. And it gives you similarity, not structure.

**Topology approach:**
- Extract atomic semantic units at write time
- Calculate relationships between ALL units (semantic + temporal)
- Store as connected graph
- At query: find entry points, traverse pre-calculated edges

The cost is upfront. The benefit is **instant multi-dimensional navigation**.

---

## How The Concept Unfolds

Every design decision follows from this core idea.

### 1. Atomic Propositions as Building Blocks

Conversations aren't monolithic. They're streams of atomic semantic units.

> "Tested Redis and Postgres, went with Postgres for ACID"

That's actually:
- Fact: "Redis evaluated"
- Fact: "PostgreSQL evaluated"
- Decision: "PostgreSQL selected"
- Reason: "ACID compliance was deciding factor"

**Why atomic?** Because topology needs **fine-grained nodes**. Coarse nodes (whole messages) create coarse connections. Fine nodes create rich, precise topology.

Each proposition = node with embedding. But the embedding is just metadata - the **topology is in the edges**.

### 2. Multi-Dimensional Edges

Pre-calculate TWO types of relationships:

**COHERENT (semantic dimension):**
- Computed at write time: cosine similarity between ALL proposition pairs
- Threshold >0.7 → create bidirectional edge
- Result: semantic neighborhood pre-mapped

**NEXT (temporal dimension):**
- Unidirectional flow through conversation sequence
- Preserves "what led to what"
- Result: story structure preserved

**Why both?** Because meaning has multiple axes:
- "What's related?" → traverse COHERENT
- "What happened next?" → traverse NEXT
- "Why did we decide X?" → traverse both (semantic to decision, temporal backward to context)

### 3. Write Cost vs Read Benefit

This is the OLAP parallel.

**Write time (conversation extraction):**
- LLM decomposes message → atomic propositions (~5-10 per message)
- Compute embeddings for each
- Calculate similarity with ALL existing propositions
- Create edges where threshold met
- Cost: ~15 seconds per conversation turn
- Scales: O(new_props × existing_props) for edge creation

**Read time (retrieval):**
- Embed query (once)
- Vector similarity → 3-5 entry propositions (fast, indexed)
- Traverse pre-calculated edges (1-2 hops)
- No re-computation, just graph walk
- Cost: milliseconds
- Scales: O(edges_traversed), not O(all_nodes)

Trade-off is explicit: pay at write (when it happens once) for speed at read (when it happens thousands of times).

Classic OLAP thinking.

### 4. Blocks as Structured Entry Points

Topology is great for exploration. But sometimes you want **direct access**.

Certain queries have patterns:
- "Where's the API link?" → need URL
- "Why did we choose X?" → need decision + reasoning

**Blocks = structured metadata attached to propositions:**

```
Resource block: {url, type, context}
Decision block: {choice, why, alternatives, confidence}
Document block: {filename, path, purpose}
```

Not separate storage - **embedded in proposition nodes**.

**Why?** Because they're entry points into the topology:
- Filter propositions by block type
- Start traversal from those nodes
- Expand through semantic/temporal edges

Blocks get you *to* the relevant part of topology. Edges let you *explore* from there.

### 5. Sleep Cycles as Topology Maintenance

Topology grows with every conversation. Without curation, it degrades:
- Too many edges → noise in traversal
- Weak propositions → dead ends
- Redundant info → duplicated paths

**Biological inspiration:** Memory consolidates what's used, forgets what's not.

**Topology analog:**

**Consolidation:**
- Track access patterns (`activation_count` on propositions)
- Frequently traversed → strengthen (higher retrieval priority)
- Semantically central (high PageRank in COHERENT graph) → strengthen
- Above threshold → mark "long-term"

**Forgetting:**
- Zero traversal for N days → mark weak
- Redundant (covered by other props) → candidate removal
- Progressive: edges fade first, then nodes

**Why it matters:** Topology quality > topology size. Sleep cycles maintain traversal quality as graph scales.

---

## What This Enables

**1. Context reconstruction, not just similarity matching**

Vector DB: "Here are 5 similar fragments"

Topology: "Here's the decision, the alternatives considered, the reasoning, and what happened after"

**2. Multi-hop reasoning**

Entry point: "PostgreSQL selected"

1-hop COHERENT: alternatives evaluated, decision criteria
1-hop NEXT backward: discussion that led to choice
1-hop NEXT forward: implementation decisions that followed

You're not searching. You're **exploring semantic neighborhood**.

**3. Dimensional flexibility**

Same entry point, different traversal strategies:
- Pure semantic: follow COHERENT only (find related ideas regardless of time)
- Pure temporal: follow NEXT only (reconstruct conversation flow)
- Hybrid: semantic to find cluster, temporal within cluster for sequence

Query determines traversal path through pre-built topology.

**4. Instant access with degradation**

Entry via blocks → O(1) to relevant propositions
Traversal → O(edges), bounded by max hops
Total: sub-second, even with millions of nodes

No full graph scan. No re-embedding. Just walk pre-calculated structure.

---

## Implementation Reality

**What's working:**

- Extraction: LLM decomposes → atomic propositions with blocks
- Embedding: OpenAI vectors for each proposition
- Edge creation: COHERENT (cosine >0.7) + NEXT (sequence)
- Storage: Neo4j (graph + vector index) + SQLite (archive)
- Basic retrieval: entry points + block filtering

**Timing:** ~15s per conversation turn (write cost, as designed)

**What's not done:**

- Bounded traversal (have edges, need walk algorithm with hop limits)
- Sleep cycles (consolidation + forgetting metrics)
- Adaptive thresholds (learn per-conversation optimal cosine cutoff)
- Cross-conversation synthesis (aggregate knowledge from multiple topologies)

**What's untested:**

- Scale beyond 1K conversations (edge density, traversal performance)
- Topology evolution (how structure changes with continuous growth)
- Forgetting impact (what happens when you prune wrong nodes)

---

## Open Questions

**1. Traversal strategy**

How many hops? Fixed depth feels rigid. Similarity decay might stop too early. Cost-based needs cost definition.

Current thinking: bounded walk with decay - `expand while (similarity > threshold × decay^hop) AND hop < max`

But values for threshold, decay, max?

**2. What makes a proposition "important" for consolidation?**

Options:
- Activation frequency (but: recency bias)
- Graph centrality (but: miss insights at periphery)
- Semantic novelty (but: how to measure?)
- Cross-conversation references (but: expensive to compute)

Probably hybrid. Weights TBD.

**3. Topology density management**

As graph grows:
- More edges = richer connections OR more noise?
- Adaptive threshold: lower for sparse graphs, higher for dense?
- Pruning strategy: remove low-weight edges periodically?

**4. Multi-topology queries**

If each conversation is a topology, how to query across them?
- Separate graphs that reference shared concept nodes?
- Meta-graph connecting conversation topologies?
- Flat merged topology with conversation-id tags?

None feel quite right yet.

---

## Why This Approach

Vector databases treat conversations as documents.

This treats them as **explorable semantic spaces**.

Difference:
- Documents are retrieved
- Spaces are navigated

For persistent memory in conversational AI, retrieval isn't enough. Need:
- Fine-grained semantic structure (atomic propositions)
- Pre-calculated relationships (write cost for read speed)
- Multi-dimensional traversal (semantic + temporal)
- Quality curation (sleep cycles)

Is it overcomplicated? Maybe.

But the concept is simple: **build topology at write time, navigate it at read time**.

Everything else follows from that.

---

## Current Status

This is a working prototype of the concept:
- Core topology building: ✓
- Basic navigation: ✓
- Advanced traversal: in progress
- Topology maintenance: not started
- Scale testing: needed

It's not a product. It's an exploration of an idea:

**What if conversation memory was a pre-calculated semantic topology instead of a searchable document store?**

Parts of the answer are promising. Parts are still unclear.

---

*This is the concept. Implementation details, setup, and testing in the repo.*

*Feedback, critiques, alternative approaches welcome.*
