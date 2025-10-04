# ReSemantic Streamlit App

Mobile-responsive conversational interface with semantic extraction.

## Features

- 💬 **Chat Interface**: Natural conversation with AI agent
- 🧠 **Semantic Extraction**: Automatic two-stage analysis (FIXED pipeline)
- 📊 **Dashboard**: Analytics, stats, and insights
- 📱 **Mobile Responsive**: Works on desktop and mobile
- 🕸️ **Neo4j Integration**: Link to knowledge graph visualization

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run:**
   ```bash
   ./run.sh
   # Or:
   streamlit run app.py
   ```

4. **Access:**
   - Desktop: http://localhost:8501
   - Mobile: http://YOUR_SERVER_IP:8501

## Structure

```
streamlit_app/
├── app.py                          # Main entry point
├── pages/
│   ├── 1_💬_Chat.py               # Chat interface
│   └── 2_📊_Dashboard.py          # Analytics dashboard
├── components/
│   ├── conversational_agent.py    # OpenAI chat agent
│   └── semantic_extractor.py      # FIXED pipeline wrapper
└── utils/
    └── session_manager.py          # Session state management
```

## Usage

1. **Start chatting** - Messages are automatically analyzed
2. **View dashboard** - See semantic units and propositions
3. **Explore graph** - Click link to Neo4j Browser

## Semantic Extraction

Each message is processed through:

**Stage 1: Semantic Unit**
- Extract meaning with rich metadata
- Resolve references and context
- Classify narrative role

**Stage 2: Propositions**
- Break into atomic statements
- No hallucinations (FIXED prompt)
- Ready for embeddings

## Mobile Features

- ✅ Responsive layout (stacks on small screens)
- ✅ Touch-friendly buttons (full width)
- ✅ Collapsible sidebar
- ✅ Optimized fonts and spacing
- ✅ Sticky input at bottom

## Next Steps

- [ ] Add Neo4j integration (insert propositions)
- [ ] Generate embeddings
- [ ] Implement vector search
- [ ] Add temporal/semantic links visualization
- [ ] Export conversation data
