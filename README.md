# ReSemantic: Living Knowledge Ecosystem

Brain-inspired conversational memory system with semantic graph storage and sleep-based consolidation.

## Overview

ReSemantic transforms conversations into a living knowledge graph through:
- **Two-stage extraction**: Messages → Semantic Units → Atomic Propositions
- **Dual storage**: Neo4j (active graph) + SQLite (immutable archive)
- **Semantic edges**: Vector similarity-based connections (COHERENT)
- **Temporal edges**: Conversation flow tracking (NEXT)
- **Fire-and-forget**: Non-blocking background extraction

## Quick Start

### Setup

```bash
# Activate environment
source langgraph_env/bin/activate

# Configure environment
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, Neo4j credentials)

# Run CLI
python3 langgraph_studio/chat_cli_batch.py
```

### Project Structure

```
/opt/resemantic/
├── config.py                    # Centralized configuration
├── graphs/
│   ├── extraction_graph.py     # LangGraph extraction pipeline
│   └── storage_nodes.py        # Modular storage operations
├── storage/
│   ├── neo4j_client.py        # Graph database client
│   ├── embeddings.py          # Vector generation (OpenAI)
│   └── archive_db.py          # SQLite archival storage
├── langgraph_studio/
│   └── chat_cli_batch.py      # Interactive CLI with fire-and-forget
└── docs/
    └── PHILOSOPHY.md           # Brain-inspired design philosophy
```

## Features

✅ **FAZA 1 Complete:**
- Two-stage extraction pipeline (Message → SU → Propositions)
- Neo4j graph with vector embeddings (1536-dim)
- Dual storage (Neo4j + SQLite)
- Temporal (NEXT) and semantic (COHERENT) edges
- Fire-and-forget async extraction
- Reasoning capture (Extended Thinking)

🔄 **FAZA 2 In Progress:**
- Sleep cycles (consolidate, strengthen, prune)
- Thematic block discovery
- Cross-block pattern extraction

🛠️ **FAZA 3 Planned:**
- Tool execution with memory
- Agent reasoning integration

## Documentation

- [PHILOSOPHY.md](docs/PHILOSOPHY.md) - Brain-inspired architecture, design principles, evolution path
- [ReSemantic_Concept.md](docs/ReSemantic_Concept.md) - Core concepts and vision
- [ReSemantic_Technical_Overview.md](docs/ReSemantic_Technical_Overview.md) - Technical deep dive

## Architecture

**Propositions = Neurons** (atomic semantic units)
**Edges = Synapses** (temporal + semantic connections)
**Context = Working Memory** (local window)
**Graph Traversal = Long-term Memory** (semantic navigation)
**Sleep Cycles = Consolidation** (strengthen, prune, discover patterns)

## Requirements

- Python 3.12+
- Neo4j database
- Anthropic API key (Claude)
- OpenAI API key (embeddings)
