# 🧪 Proposition Extraction Experiment

## Hypothesis
**Atomic propositions produce better embeddings than semantic unit summaries for retrieval.**

## Architecture

### Two-Layer System

```
Conversation Message
        ↓
    ┌───┴───┐
    ↓       ↓
Semantic   Propositions
  Unit     (atomic facts)
    ↓           ↓
Narrative   Embeddings
Structure   + Retrieval
```

### Layer 1: Semantic Units (NOT for embeddings)
- **Purpose**: Narrative structure, conversation flow
- **Format**: High-level summary
- **Example**: "Assistant explained how propositionalization improves embedding quality"
- **Problem**: Too abstract for semantic matching

### Layer 2: Propositions (FOR embeddings)
- **Purpose**: Vector search, precise retrieval
- **Format**: Atomic, self-contained facts
- **Example**:
  - "Propositionalization breaks text into atomic statements"
  - "Each proposition expresses one verifiable fact"
  - "Atomic propositions reduce embedding dilution"

## What We're Testing

### Method A: Baseline
- Direct LLM prompting
- Single-shot extraction
- No optimization

### Method B: DSPy
- Structured signatures with `dspy.ChainOfThought`
- Type hints and descriptions
- Potential for few-shot optimization
- Better prompt engineering

## Evaluation Metrics

1. **Proposition Quality**
   - Count and granularity
   - Atomicity (one fact per proposition)
   - Self-containment (resolved references)
   - Concept coverage

2. **Embedding Effectiveness**
   - Retrieval accuracy with test queries
   - Cosine similarity scores
   - Top-K precision

3. **Comparison**
   - Which produces better matches?
   - Quality vs quantity trade-off
   - Practical usability

## Test Data

Using our own conversation about:
- Semantic units
- Propositionalization concepts
- spaCy limitations
- Embedding challenges

**Perfect because it contains:**
- Short responses ("Da", "Exact") that need expansion
- Technical explanations that need decomposition
- Coreferențes ("ea", "asta") that need resolution
- Multiple topics requiring clear segmentation

## Running the Experiment

```bash
# 1. Add API key to .env
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Run experiment
./run_experiment.sh

# 3. Review results
cat comparison_results.json
```

## Expected Insights

### If DSPy wins:
- Better structured prompting helps
- Few-shot examples improve consistency
- Type hints guide extraction quality

### If Baseline comparable:
- Problem is simple enough
- Current LLMs handle it well without optimization
- DSPy overhead not justified

### Either way:
- Validate that propositions > summaries for embeddings
- Establish baseline for graph-based memory system
- Inform Living Knowledge Ecosystem architecture

## Next Steps After Results

1. **If successful**: Integrate into production memory system
2. **Add metadata**: Link propositions to semantic units
3. **Graph construction**: Temporal + semantic edges between propositions
4. **Sleep cycles**: Implement coherence-based consolidation
5. **Scale testing**: Longer conversations, multiple topics

---

*This experiment validates the foundational assumption of the Living Knowledge Ecosystem: that atomic propositions, not summaries, should be embedded for retrieval.*
