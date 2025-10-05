# ReSemantic: Semantic Memory for Conversational AI

*O discuție tehnică despre cum am abordat problema memoriei persistente în conversații*

---

## Problema pe care o rezolvăm

LLM-urile au memorie excelentă - dar doar în cadrul unei conversații. Oprești sessionul, contextul dispare. Revii după 3 zile, AI-ul nu știe nimic despre ce ați discutat.

Răspunsul obișnuit: RAG cu vector database. Caută prin conversații trecute cu embedding similarity, injectează în context.

**Funcționează, dar superficial.** Găsești ce e "similar" semantic, dar pierzi structura conversației, relațiile între idei, evoluția gândirii.

Problema reală nu e că nu poți găsi informații. E că **nu poți naviga prin ele**.

---

## Insight-ul de bază: Atomic Propositions ca Graph Nodes

Am pornit de la o observație simplă: **conversațiile sunt streams de propoziții atomice**.

Când cineva spune:
> "Am testat Redis și MongoDB, dar am ales PostgreSQL pentru ACID compliance și stability"

Nu e o unitate indivizibilă. Sunt **4 propoziții atomice**:
1. "Testare efectuată pentru Redis ca opțiune database"
2. "Testare efectuată pentru MongoDB ca opțiune database"  
3. "PostgreSQL selectat ca soluție finală"
4. "Criteriile de selecție au fost ACID compliance și stability"

Fiecare propoziție = **node în graf cu propriul vector embedding**.

**De ce atomice?** Pentru că retrieval-ul nu funcționează la nivel de mesaj întreg. Mesajul conține prea multe idei. Vrei granularitate - să găsești *exact* bucata relevantă, nu tot paragraful.

---

## De ce LLM pentru descompunere, nu NLP clasic?

Alternativa: dependency parsing, coreference resolution, semantic role labeling - instrumentele NLP tradiționale.

**Problema:** Sunt fragile la conversații reale.

Conversațiile nu sunt proză bine formată:
- Referințe implicite ("da, perfect" - da la ce?)
- Context necesar pentru înțelegere ("folosim asta" - asta = ce?)
- Nuanțe semantice ("pare ok" vs "e exact ce trebuie")

LLM-ul face ceva pe care NLP clasic nu poate: **semantic understanding în context**. Nu doar parseză, *înțelege*.

Exemple concrete:

**Input:** "da, asta e soluția"

**NLP parsing:** subject=asta, verb=e, complement=soluția (useless fără context)

**LLM cu context:** "User confirmă alegerea PostgreSQL ca soluție database" (semantic unit complet)

---

LLM-ul rezolvă și coreferences:
- "l-am configurat așa" → ce sistem, ce configurație?
- "merge perfect" → ce anume merge, pentru ce scop?

Nu doar identifică pronumele - **reconstituie semantica completă** folosind întreaga conversație ca referință.

Prețul: latency (~15s per extraction). Beneficiul: propositions *self-contained* și semantic corecte.

---

## Graph Traversal vs Vector Similarity

Aici e diferența fundamentală față de vector DB clasic.

**Vector DB tradițional:**
- Query → top K similar vectors
- Context = lista de K fragmente
- Fiecare fragment independent

**Graph approach:**
- Query → entry points (3-5 propositions via similarity)
- **Expand** prin semantic edges (COHERENT relationships)
- Context = **subgraf conectat**

### De ce face diferența?

**1. Contextul se desfășoară natural**

Entry point: "PostgreSQL ales pentru ACID compliance"

Traversare 1-hop prin COHERENT edges:
- → "Testare MongoDB efectuată anterior" (alternative consideration)
- → "Redis evaluat pentru caching use case" (related decision)
- → "Performance benchmarks comparate între opțiuni" (decision basis)

Rezultat: Nu doar *ce* s-a decis, ci **de ce și în contrast cu ce alternative**.

**2. Temporal flow disponibil**

NEXT edges (temporal) permit:
- "Cum s-a ajuns la decizie?" → urmărește backward prin NEXT
- "Ce a urmat după?" → forward traversal

Conversația nu e static snapshot - e *story* navigabilă.

**3. Multi-hop reasoning**

Vector similarity = 1-hop (query → results). 

Graph = bounded traversal (1-2 hops cu threshold decay):
- Hop 1: direct relevant (cosine >0.7)
- Hop 2: tangențial relevant (cosine >0.6, dar conectat la Hop 1)

Găsești și idei *adiacente semantic*, nu doar matches directe.

---

## Blocks: Agenda pentru Access Rapid

Graph traversal e puternic, dar uneori vrei **shortcuts**.

Observație: Anumite întrebări au pattern-uri:
- "Unde era linkul?" → caută URL
- "De ce am ales X?" → caută decizie + reasoning
- "Unde e config-ul?" → caută file path

**Blocks = metadata structurată extrasă automat:**

**Resource blocks:**
- URL + type (docs/api/tool)
- Context: pentru ce e relevant

**Decision blocks:**
- Choice (ce s-a decis)
- **WHY** (reasoning explicit)
- Alternatives (ce s-a respins)
- Confidence level

**Document blocks:**
- Filename + path
- Purpose (la ce servește)

### De ce duplicate în fiecare proposition?

**Alternativa:** Metadata doar în semantic units, propositions linkuiesc.

**Problema:** Retrieval = multi-hop (prop → SU → metadata). Latency + complexity.

**Soluția:** Duplicate blocks în props.
- Write penalty: once per extraction
- Read benefit: thousands of retrievals cu zero joins

Trade-off clar: storage space (acceptabil) vs retrieval speed (critical).

### Utilizare

Blocks permit **filtered traversal**:
- "Link-uri despre authentication" → start cu block_metadata.resource_url CONTAINS "auth"
- "De ce am respins MongoDB?" → filter decision_choice + search alternatives

Nu înlocuiesc graph traversal - îl **focalizează**.

---

## Sleep Cycles: Active Forgetting

Inspirație biologică: creierul uman nu reține tot egal.

**Consolidare (REM sleep analog):**
- Reactivări repetate → strengthening
- Propositions accesate des → `activation_count++`
- Threshold → upgrade la "long-term" memory

**Uitare selectivă (synaptic pruning):**
- Low activation după N zile → mark as weak
- Redundant info (covered de alte props) → candidate removal
- Progressive fade: edges → metadata → eventual node

**De ce e necesar?**

Graph growth = linear cu conversații. Fără cleanup:
- Retrieval noise (prea multe results)
- Traversal confusion (edges către propositions irelevante)
- Storage bloat (evident)

**Întrebare deschisă:** Ce metrics pentru "important"?
- Activation count alone? (risc: frecvent ≠ valoros)
- Semantic centrality? (PageRank în COHERENT graph)
- User signals? (explicit feedback pe retrieval)

Probabil hybrid. Încă explorăm.

---

## Stadiul Actual

### Ce funcționează

**Extraction (2-stage LLM pipeline):**
- Semantic units cu context resolution
- Atomic propositionalization
- Blocks extraction automat
- Timing: ~15s per turn (user + assistant)

**Storage (dual-layer):**
- Neo4j pentru graph (nodes + edges + vector index)
- SQLite pentru archive (immutable, source of truth)

**Retrieval (basic):**
- Embedding similarity → entry points
- Block filtering functional
- Context assembly cu metadata inline

### Ce lipsește

**Graph traversal avansat:**
- Bounded expansion (max hops, cost decay)
- Temporal boosting (recent > old la same similarity)
- Concept clustering (grup related props)

**Sleep cycles:**
- Metrics pentru importance (activation + structure + signals?)
- Consolidation strategy (când upgrade?)
- Forgetting policy (ce threshold pentru removal?)

**Scalability:**
- Testing la 10K+ conversations
- Performance optimization (query plans, index tuning)
- Monitoring (graph health metrics)

---

## Open Questions - Invit la Discuție

**1. Traversal stopping criteria**

Când oprești expansion-ul în graf? 
- Fixed hops (rigid)
- Similarity threshold decay (poate miss context)
- Cost-based (cum măsori "cost"?)

Probabil combinație, dar care weights?

**2. Consolidation metrics**

Ce definește "important" pentru long-term retention?
- Activation frequency (but: echo chambers)
- Graph centrality (but: orphan insights)
- Cross-conversation references (promising, dar complex)

**3. Context window management**

LLM-uri cu 200K tokens = multe propositions. Dar nu vrei totul în context.

Strategy:
- Summary level pentru overview (semantic units ca "super-nodes")
- Detail pe request (expand specific branches)
- Progressive disclosure (feed minimal, expand on demand)

Cum alegi ce expui vs ce ții în graf pentru deep dive?

**4. Cross-conversation knowledge**

Propositions cu same concepts în conversații diferite = oportunitate pentru meta-insights.

Exemplu: "PostgreSQL" menționat în 5 conversații → cluster?

Beneficii:
- "Ce știi despre PostgreSQL?" → aggregate din toate sursele
- Pattern detection (recurring decisions, common issues)

Challenges:
- Conflict resolution (contradicții între conversații)
- Attribution (ce vine de unde)
- Privacy (dacă e multi-user)

---

## Why This Matters

Vector databases cu RAG = search engine peste conversații.

Graph semantic memory = **navigable knowledge structure**.

Diferența:
- Search găsește fragmente
- Graph reconstituie **gândire**

Pentru AI conversațional persistent, trebuie mai mult decât retrieval. Trebuie **memory architecture**.

ReSemantic e un experiment în asta: treat conversations ca semantic streams, decompose atomic, store traversable.

Funcționează? Partial. 

E complet? Nu. 

E interesant? Cred că da.

---

*Documentul e deschis pentru critique. Dacă vezi probleme în approach, alternative mai bune, sau vrei să discuți implementation - let's talk.*

*Setup & testing: vezi README în repo.*
