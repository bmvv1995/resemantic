# ReSemantic: Persistent Semantic Memory for Conversations

*How I'm thinking about the conversation memory problem*

---

Look, LLMs are getting ridiculous at conversation - until you close the tab. Then they're goldfish. 

The usual fix is RAG: chunk conversations, embed them, similarity search when needed. Works okay for "find that thing we discussed," but it's fundamentally limited. You're searching through text fragments, not navigating through *thought*.

What if we treated conversations differently? Not as documents to index, but as semantic graphs to traverse.

---

## The Core Idea: Conversations Are Streams of Atomic Propositions

When someone says:
> "I tested Redis and Postgres, went with Postgres for the ACID guarantees"

That's not one thing. It's actually:
- A fact: "Redis was evaluated as option"
- A fact: "PostgreSQL was evaluated as option"  
- A decision: "PostgreSQL was selected"
- A reason: "ACID compliance was the deciding factor"

Each piece is atomic, verifiable, self-contained. Each piece should be a **node in a graph**, with its own embedding.

Why atomic? Because retrieval doesn't work at the message level. Messages contain too much. If someone later asks "why did we pick Postgres?", you don't want the whole paragraph about testing - you want the specific decision + reasoning.

---

## Why LLM Decomposition Instead of NLP

You could use classic NLP: dependency parsing, coreference resolution, semantic role labeling. I tried.

**It breaks on real conversations.**

People don't talk in well-formed sentences:
- "Yeah, that works" - what works? Need context
- "Let's use that for the API" - that = what exactly?
- "Sounds good, go for it" - go for what decision?

NLP parsers see syntax. LLMs understand *semantics in context*.

Example:

**Input:** "da, perfect, folosim asta"

**Dependency parser:** subject=noi, verb=folosim, object=asta *(useless)*

**LLM with conversation context:** "User confirms selection of PostgreSQL database for the application" *(complete semantic unit)*

The LLM doesn't just identify pronouns - it **reconstructs the full meaning** using the entire conversation as context. That's not something regex or parse trees can do.

Trade-off: 15 seconds per extraction vs instant parsing. But you get propositions that are actually *understandable* on their own.

---

## Graph Structure: Why It Matters

Vector databases give you similarity search. That's an entry point, not a solution.

Here's the difference:

**Traditional vector DB:**
1. Embed query
2. Cosine similarity → top 5 results
3. Return those 5 chunks

**Graph approach:**
1. Embed query → find 3-5 entry propositions (similarity)
2. **Traverse** through semantic edges
3. Return connected subgraph

### What does traversal get you?

**Context unfolds naturally.**

Say you hit proposition: "PostgreSQL selected for ACID compliance"

One hop through semantic edges (cosine > 0.7):
- → "MongoDB considered but rejected" 
- → "Redis evaluated for caching use case"
- → "Performance benchmarks showed Postgres advantage"

You don't just get *the decision* - you get **the reasoning, alternatives, and evidence**. 

The graph structure captures how ideas relate, not just what words match.

### Two types of edges:

**COHERENT** (semantic similarity):
- Bidirectional
- Threshold: cosine > 0.7
- Connects semantically related propositions

**NEXT** (temporal flow):
- Unidirectional  
- Preserves conversation sequence
- Enables "story" navigation

**COHERENT** gives you semantic neighborhood. **NEXT** gives you temporal context. Together: you can both explore similar ideas AND follow how the conversation evolved.

---

## Why Not Just Vector Search With Post-Processing?

Valid question. Why the graph complexity?

**Because relationships matter more than similarity.**

Vector search finds what's *similar to your query*. Graph traversal finds what's *connected to what you found*.

Example query: "What did we decide about databases?"

Vector search returns:
- "PostgreSQL selected" (high similarity)
- "Database choice finalized" (high similarity)  
- "ACID compliance important" (medium similarity)

Graph traversal from same entry points returns:
- Direct: PostgreSQL selection
- 1-hop: Alternatives evaluated (Redis, MongoDB)
- 1-hop: Decision criteria (ACID, performance)
- 1-hop: Implementation considerations
- 2-hop: Related architecture decisions

The *structure* encodes relationships that embeddings alone miss.

Plus: you can traverse backward (what led to this?) or forward (what followed?) through NEXT edges. Conversations have sequence - the graph preserves it.

---

## Blocks: Structured Metadata as Shortcuts

Graph traversal is powerful but sometimes you want direct access.

Certain questions have patterns:
- "Where's that API link?" → looking for URL
- "Why did we choose X?" → looking for decision + reasoning  
- "Where's the config file?" → looking for filepath

**Blocks are structured metadata extracted and attached to each proposition:**

**Resource block:**
```
resource_url: https://api.example.com/docs
resource_type: documentation
discussed_context: "authentication implementation"
```

**Decision block:**
```
decision_choice: "OAuth 2.0"
decision_reason: "Industry standard, better security than custom"
decision_alternatives: ["Basic Auth", "API Keys"]  
decision_confidence: "high"
```

**Document block:**
```
doc_filename: "auth_config.yaml"
doc_location: "/opt/configs/auth_config.yaml"
doc_purpose: "OAuth provider settings"
```

### How they're used:

Not as replacement for graph traversal - as **filters** to focus it.

"Show me decisions about authentication" → 
1. Filter propositions where block_metadata.decision_choice contains "auth"
2. Start traversal from those nodes
3. Expand through COHERENT edges

You get both: direct access to structured info + graph context around it.

---

## Sleep Cycles: The Hard Problem

Here's what I haven't solved yet.

Graph grows linearly with conversations. Without cleanup:
- Retrieval gets noisy (too many results)
- Traversal gets confused (edges to irrelevant old stuff)  
- Storage bloats (obviously)

Biological memory has a solution: consolidation + forgetting.

**Consolidation (what to keep):**
- Frequent access → strengthen (increment activation_count)
- High semantic centrality → strengthen (PageRank in COHERENT graph)
- Explicit user signals → strengthen (thumbs up on retrieval)

Above threshold → mark as "long-term", higher retrieval priority.

**Forgetting (what to fade):**
- Zero activation for N days → mark as weak
- Redundant (covered by other propositions) → candidate removal
- Progressive deletion: edges first, then metadata, eventually node

**The open question: what metrics determine "important"?**

- Activation count alone = recency bias
- Centrality alone = miss isolated insights  
- User feedback alone = sparse signals

Probably needs hybrid scoring. Still exploring.

Another issue: **what about wrong information that was later corrected?**

If conversation on Monday says "use Redis" but Friday says "actually no, use Postgres", both are in the graph. Sleep cycles should favor the later, more current decision. But how to detect that pattern automatically?

---

## Current State

**Working:**
- Two-stage extraction (semantic units → atomic propositions)
- Block metadata extraction via LLM
- Neo4j storage with vector index
- SQLite archive (immutable log)
- Basic retrieval (similarity + block filtering)
- Edge creation (COHERENT + NEXT)

**Timing:** ~15 seconds per conversation turn. Not instant, but propositions are high quality.

**Not working yet:**
- Graph traversal expansion (have the edges, haven't implemented bounded walks)
- Temporal boosting (recent vs old at same similarity)
- Sleep cycles (consolidation + forgetting)

**Untested:**
- Scale beyond 1000 conversations
- Cross-conversation knowledge synthesis  
- Conflict resolution (contradicting info across conversations)

---

## Design Choices I'm Second-Guessing

**1. LLM for everything**

Pro: Semantic understanding, context resolution  
Con: 15 second latency, API costs

Alternative: Hybrid - LLM for complex semantic work, fast NLP for simple decomposition.

Could optimize: use LLM only when coreference detected, otherwise fast path with spaCy. Haven't tested if the complexity is worth it.

**2. Cosine threshold for COHERENT edges (0.7)**

Arbitrary. Works in practice, but probably should be adaptive:
- Lower threshold for sparse graphs (few propositions)
- Higher for dense (avoid noise)

Or: learn threshold per conversation based on proposition density.

---

## What I'd Do Differently

If starting over:

**1. Prototype sleep cycles earlier**

Graph growth is the real challenge. Should've tackled it before retrieval optimization.

**2. Instrument everything from day one**

Need metrics: retrieval latency, traversal hop distribution, activation patterns, edge density over time.

Building them retroactively is painful.

**3. Test at scale sooner**

Easy to make architecture decisions with 100 conversations. Different reality at 10,000.

---

## Open Problems I'm Stuck On

**1. Traversal stopping criteria**

How many hops? Fixed depth (rigid), similarity decay (might stop too early), or cost-based (how to measure cost)?

Current thinking: start at entry nodes, expand while (similarity > threshold * decay_factor^hop_count) AND hop_count < max_hops.

But what values for threshold, decay, max_hops?

**2. What makes a proposition "important"?**

For consolidation, need scoring. Options:
- Activation frequency (but: recency bias, echo chambers)
- Graph centrality (but: miss peripheral insights)  
- Semantic diversity (novel info vs repeated)
- Cross-conversation references (appears in multiple contexts)

Probably weighted combination. But what weights?

**3. Handling corrections and updates**

User says "use Redis" then later "actually, Postgres is better."

Both are in graph. Sleep cycles should fade first, keep second. But detection is hard:
- Same concepts (database choice)
- Temporal sequence (later corrects earlier)
- Semantic contradiction (different choices)

Need pattern: if (same_concepts AND later_timestamp AND contradicting_conclusion) → mark earlier as superseded.

Haven't implemented this.

**4. Context window limits**

LLM has 200K tokens. Graph can have millions of propositions.

Can't feed everything. Need strategy:
- Tiered retrieval: summary → detail on demand
- Progressive disclosure: start minimal, expand if needed
- Compression: semantic units as "chapter summaries"

Which to expose in context vs keep in graph for deep-dive?

---

## Why This Approach

Vector databases with RAG are search engines over conversations.

This is trying to be a **memory system**.

Difference:
- Search finds fragments that match
- Memory reconstructs context that matters

For persistent conversational AI, similarity search isn't enough. Need:
- Structural relationships (graph)
- Semantic granularity (atomic propositions)  
- Temporal flow (sequence preservation)
- Access patterns (blocks for common queries)
- Active curation (sleep cycles)

Is it overcomplicated? Maybe.

Is it necessary? For real memory-like behavior, I think so.

Does it work? Parts of it. Still finding out.

---

## What's Next

**Immediate:**
- Implement bounded graph traversal (have edges, need walk algorithm)
- Test at 5K+ conversations (performance, edge density)

**Soon:**
- Sleep cycles MVP (simple activation-based consolidation)
- Temporal boosting (recent vs old)

**Eventually:**
- Cross-conversation synthesis (aggregate knowledge)
- Adaptive thresholds (learn per conversation)
- Conflict resolution (handle contradictions)

**Open for:**
- Feedback on approach
- Alternative architectures
- Collaboration on sleep cycles
- Scale testing

---

*This is a work in progress. Some parts work well, others don't. If you see problems or have better ideas, I want to hear them.*

*Technical details, setup, testing: check the repo README.*
