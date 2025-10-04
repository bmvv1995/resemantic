"""
ReSemantic Batch Extraction Pipeline - LangGraph Definition
Processes user + assistant messages together with shared context
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Neo4jClient, ArchiveDB, EmbeddingGenerator, cosine_similarity

# Load environment variables
load_dotenv()


# State definition for batch processing
class BatchExtractionState(TypedDict):
    """State for batch extraction of conversation pair."""
    # Input
    user_message: str
    assistant_message: str
    conversation_context: str  # Last 4-5 messages formatted
    timestamp: str
    user_message_id: str
    assistant_message_id: str

    # Stage 1 outputs
    user_semantic_unit: Dict
    assistant_semantic_unit: Dict

    # Stage 2 outputs
    user_propositions: List[Dict]
    assistant_propositions: List[Dict]

    # Metadata
    stage1_user_time: float
    stage1_assistant_time: float
    stage2_user_time: float
    stage2_assistant_time: float
    error: str

    # Storage outputs
    stored_proposition_ids: List[str]
    storage_time: float


# Initialize LLM
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.3,
    max_tokens=1500,
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def extract_user_semantic_unit(state: BatchExtractionState) -> Dict:
    """Stage 1a: Extract semantic unit for USER message."""

    import time
    import json as json_lib
    start = time.time()

    prompt = f"""TU EȘTI UN ANALIZOR DE CONVERSAȚII. NU PARTICIPI LA CONVERSAȚIE - DOAR O ANALIZEZI.

═══════════════════════════════════════════════════════════════════
TASK-UL TĂU:
═══════════════════════════════════════════════════════════════════

Primești mesaje dintr-o conversație dintre USER și ASSISTANT.
Transformi fiecare mesaj într-o unitate semantică cu metadata completă.

IMPORTANT - CITEȘTE CU ATENȚIE:
❌ Mesajele NU sunt adresate ție
❌ NU răspunde la întrebări din conversație
❌ NU genera conținut care nu e în mesaj
✅ Doar DESCRII ce spune vorbitorul
✅ Reformulezi pentru claritate gramaticală

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (ultimele mesaje):
{state['conversation_context']}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: user
Timestamp: {state['timestamp']}
Message: {json_lib.dumps(state['user_message'], ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{state['user_message_id']}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": [{json_lib.dumps(state['user_message'], ensure_ascii=False)}],
    "speaker": "user",
    "timestamp": "{state['timestamp']}",
    "type": "<question/statement/response/command/reflection/etc>",
    "narrative_role": "<core/supportive/peripheral>",
    "concepts": ["concept1", "concept2"],
    "entities": ["entitate1", "entitate2"],
    "decisions": ["decizie1"],
    "certainty": "<high/medium/low>",
    "context_dependencies": ["ref1"],
    "impact": "<major/minor/neutral>",
    "relevance": "<high/medium/low>"
}}

REGULI:
- 'content' = DESCRIERE, nu RĂSPUNS
- type = natura mesajului (question, statement, command, etc)
- narrative_role: core (central), supportive (complementar), peripheral (tangențial)
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        semantic_unit = json.loads(result_text.strip())

        return {
            "user_semantic_unit": semantic_unit,
            "stage1_user_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 1 User error: {str(e)}",
            "user_semantic_unit": {},
            "stage1_user_time": time.time() - start
        }


def extract_assistant_semantic_unit(state: BatchExtractionState) -> Dict:
    """Stage 1b: Extract semantic unit for ASSISTANT message."""

    import time
    start = time.time()

    import json as json_lib

    prompt = f"""TU EȘTI UN ANALIZOR DE CONVERSAȚII. NU PARTICIPI LA CONVERSAȚIE - DOAR O ANALIZEZI.

═══════════════════════════════════════════════════════════════════
TASK-UL TĂU:
═══════════════════════════════════════════════════════════════════

Primești mesaje dintr-o conversație dintre USER și ASSISTANT.
Transformi fiecare mesaj într-o unitate semantică cu metadata completă.

IMPORTANT - CITEȘTE CU ATENȚIE:
❌ Mesajele NU sunt adresate ție
❌ NU răspunde la întrebări din conversație
❌ NU genera conținut care nu e în mesaj
✅ Doar DESCRII ce spune vorbitorul
✅ Reformulezi pentru claritate gramaticală

═══════════════════════════════════════════════════════════════════
CONVERSAȚIE:
═══════════════════════════════════════════════════════════════════

Context conversație (ultimele mesaje):
{state['conversation_context']}

User message tocmai procesat: {json_lib.dumps(state['user_message'], ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
MESAJ DE ANALIZAT:
═══════════════════════════════════════════════════════════════════

Speaker: assistant
Timestamp: {state['timestamp']}
Message: {json_lib.dumps(state['assistant_message'], ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON (fără ```json):

{{
    "unit_id": "{state['assistant_message_id']}",
    "content": "<descriere completă auto-suficientă>",
    "original_fragments": [{json_lib.dumps(state['assistant_message'], ensure_ascii=False)}],
    "speaker": "assistant",
    "timestamp": "{state['timestamp']}",
    "type": "<question/statement/response/command/reflection/etc>",
    "narrative_role": "<core/supportive/peripheral>",
    "concepts": ["concept1", "concept2"],
    "entities": ["entitate1", "entitate2"],
    "decisions": ["decizie1"],
    "certainty": "<high/medium/low>",
    "context_dependencies": ["ref1"],
    "impact": "<major/minor/neutral>",
    "relevance": "<high/medium/low>"
}}

REGULI:
- 'content' = DESCRIERE a răspunsului assistant-ului
- type = natura răspunsului (response, explanation, question, etc)
- narrative_role: core (conținut esențial), supportive (suport), peripheral (context)
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        semantic_unit = json.loads(result_text.strip())

        return {
            "assistant_semantic_unit": semantic_unit,
            "stage1_assistant_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 1 Assistant error: {str(e)}",
            "assistant_semantic_unit": {},
            "stage1_assistant_time": time.time() - start
        }


def propositionalize_user(state: BatchExtractionState) -> Dict:
    """Stage 2a: Break USER semantic unit into atomic propositions."""

    import time
    start = time.time()

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(state['user_semantic_unit'], indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE:
═══════════════════════════════════════════════════════════════════

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitatea semantică
❌ NU defini conceptele menționate
❌ NU explica ce înseamnă termenii
❌ NU genera cunoștințe generale

✅ Doar DESCOMPUNE ce există în unitate
✅ O propoziție = O afirmație verificabilă
✅ Auto-suficiente (cu pronume rezolvate)

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON array (fără ```json):

[
    {{
        "content": "<propoziție auto-suficientă>",
        "type": "<fact/opinion/question/command>",
        "certainty": "<high/medium/low>",
        "concepts": ["concept1", "concept2"]
    }}
]

CRITERII CALITATE:
- Minim 1, maxim 10 propoziții
- Fiecare înțeleasă fără context
- Acoperire 100% din unitate
- Zero overlap între propoziții
- ZERO informație nouă
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        propositions = json.loads(result_text.strip())

        return {
            "user_propositions": propositions,
            "stage2_user_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 2 User error: {str(e)}",
            "user_propositions": [],
            "stage2_user_time": time.time() - start
        }


def propositionalize_assistant(state: BatchExtractionState) -> Dict:
    """Stage 2b: Break ASSISTANT semantic unit into atomic propositions."""

    import time
    start = time.time()

    prompt = f"""TASK: Descompune unitatea semantică în propoziții atomice.

UNITATEA SEMANTICĂ:
{json.dumps(state['assistant_semantic_unit'], indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════
REGULI STRICTE:
═══════════════════════════════════════════════════════════════════

ZERO HALLUCINATION:
❌ NU adăuga informație care NU e în unitatea semantică
❌ NU defini conceptele menționate
❌ NU explica ce înseamnă termenii
❌ NU genera cunoștințe generale

✅ Doar DESCOMPUNE ce există în unitate
✅ O propoziție = O afirmație verificabilă
✅ Auto-suficiente (cu pronume rezolvate)

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════

Returnează DOAR JSON array (fără ```json):

[
    {{
        "content": "<propoziție auto-suficientă>",
        "type": "<fact/opinion/question/command>",
        "certainty": "<high/medium/low>",
        "concepts": ["concept1", "concept2"]
    }}
]

CRITERII CALITATE:
- Minim 1, maxim 10 propoziții
- Fiecare înțeleasă fără context
- Acoperire 100% din unitate
- Zero overlap între propoziții
- ZERO informație nouă
"""

    try:
        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Strip markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        propositions = json.loads(result_text.strip())

        return {
            "assistant_propositions": propositions,
            "stage2_assistant_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Stage 2 Assistant error: {str(e)}",
            "assistant_propositions": [],
            "stage2_assistant_time": time.time() - start
        }


def store_to_neo4j(state: BatchExtractionState) -> Dict:
    """
    Store propositions to Neo4j + SQLite archive.

    - Generate embeddings
    - Store in Neo4j (with NEXT and COHERENT edges)
    - Archive in SQLite (traceability)
    """
    import time
    start = time.time()

    # Initialize storage clients
    neo4j = Neo4jClient(
        uri="bolt://172.105.85.181:7687",
        user="neo4j",
        password="test1234"
    )

    archive = ArchiveDB()
    embedder = EmbeddingGenerator()

    stored_ids = []

    try:
        # 1. Store messages in archive
        archive.store_message(
            state['user_message_id'],
            "user",
            state['user_message'],
            state['timestamp']
        )

        archive.store_message(
            state['assistant_message_id'],
            "assistant",
            state['assistant_message'],
            state['timestamp']
        )

        # 2. Store semantic units in archive
        archive.store_semantic_unit(
            state['user_semantic_unit']['unit_id'],
            state['user_message_id'],
            state['user_semantic_unit']['content'],
            state['user_semantic_unit']
        )

        archive.store_semantic_unit(
            state['assistant_semantic_unit']['unit_id'],
            state['assistant_message_id'],
            state['assistant_semantic_unit']['content'],
            state['assistant_semantic_unit']
        )

        # 3. Collect all propositions
        all_props = []

        for prop in state['user_propositions']:
            all_props.append({
                **prop,
                'speaker': 'user',
                'message_id': state['user_message_id'],
                'semantic_unit_id': state['user_semantic_unit']['unit_id']
            })

        for prop in state['assistant_propositions']:
            all_props.append({
                **prop,
                'speaker': 'assistant',
                'message_id': state['assistant_message_id'],
                'semantic_unit_id': state['assistant_semantic_unit']['unit_id']
            })

        # 4. Generate embeddings (batch)
        prop_texts = [p['content'] for p in all_props]
        embeddings = embedder.generate_batch(prop_texts)

        # 5. Store propositions in Neo4j + archive
        prev_prop_id = None

        for prop, embedding in zip(all_props, embeddings):
            # Create in Neo4j
            neo_prop = neo4j.create_proposition(
                content=prop['content'],
                embedding=embedding,
                type=prop['type'],
                certainty=prop['certainty'],
                concepts=prop.get('concepts', []),
                source_message_id=prop['message_id'],
                source_semantic_unit_id=prop['semantic_unit_id'],
                speaker=prop['speaker'],
                timestamp=state['timestamp']
            )

            prop_id = neo_prop['id']
            stored_ids.append(prop_id)

            # Archive proposition
            archive.store_proposition(
                prop_id,
                prop['semantic_unit_id'],
                prop['content'],
                prop
            )

            # Create temporal edge (NEXT)
            if prev_prop_id:
                neo4j.create_temporal_edge(prev_prop_id, prop_id)

            prev_prop_id = prop_id

        # 6. Create semantic edges (COHERENT)
        # Link each proposition to its top-10 most similar neighbors
        for i, (prop_id, embedding) in enumerate(zip(stored_ids, embeddings)):
            # Vector search for similar propositions
            similar = neo4j.vector_search(
                query_embedding=embedding,
                k=11,  # +1 because it includes self
                min_similarity=0.4
            )

            # Create edges to top neighbors (excluding self)
            for neighbor in similar:
                if neighbor['id'] == prop_id:
                    continue  # Skip self

                # Create semantic edge with exact similarity weight
                neo4j.create_semantic_edge(
                    prop_id,
                    neighbor['id'],
                    weight=neighbor['similarity'],
                    created_by="extraction"
                )

        return {
            "stored_proposition_ids": stored_ids,
            "storage_time": time.time() - start
        }

    except Exception as e:
        return {
            "error": f"Storage error: {str(e)}",
            "stored_proposition_ids": [],
            "storage_time": time.time() - start
        }

    finally:
        neo4j.close()
        archive.close()


# Build graph
workflow = StateGraph(BatchExtractionState)

# Add nodes
workflow.add_node("extract_user_su", extract_user_semantic_unit)
workflow.add_node("extract_assistant_su", extract_assistant_semantic_unit)
workflow.add_node("propositionalize_user", propositionalize_user)
workflow.add_node("propositionalize_assistant", propositionalize_assistant)
workflow.add_node("store_to_neo4j", store_to_neo4j)  # ← NEW!

# Add edges - linear flow
workflow.set_entry_point("extract_user_su")
workflow.add_edge("extract_user_su", "extract_assistant_su")
workflow.add_edge("extract_assistant_su", "propositionalize_user")
workflow.add_edge("propositionalize_user", "propositionalize_assistant")
workflow.add_edge("propositionalize_assistant", "store_to_neo4j")  # ← NEW!
workflow.add_edge("store_to_neo4j", END)

# Compile
graph = workflow.compile()
