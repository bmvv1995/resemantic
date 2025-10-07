"""
Extraction Nodes V2 - Optimized Pipeline
==========================================

Key differences from V1:
1. User extraction: Focus on FACTS (URLs, specs, data)
2. Reasoning extraction: Focus on LOGIC (decisions, alternatives, drifts)
3. Assistant message: NO extraction (stored RAW only)

Philosophy:
- User message = INPUT DATA (concrete facts)
- Reasoning = PROCESSING (interpretations + decisions)
- Assistant response = OUTPUT DISPLAY (presentation only)
"""

from typing import Dict
from langchain_anthropic import ChatAnthropic
from config import ExtractionConfig
import json
import time


# ============================================
# V2 PROMPTS - USER EXTRACTION (FACTS FOCUS)
# ============================================

USER_EXTRACTION_PROMPT_V2 = """You are extracting CONCRETE FACTS from user input.

Focus on DATA, not interpretations:
- Resource URLs (API endpoints, docs, tools)
- Technical specifications (timeouts, versions, configs)
- Concrete numbers (rates, limits, percentages)
- Error messages (exact text)
- File paths and names
- Technology names
- Problem descriptions (factual)

DO NOT interpret or add context - just extract what user explicitly stated.

User message:
{user_message}

Previous context (for reference only):
{context}

Extract as JSON:
{{
    "content": "Summary of user's factual statements",
    "type": "question" | "statement" | "problem_report",
    "certainty": "high",
    "narrative_role": "core",
    "concepts": ["technology_name", "domain_concept"],
    "block_metadata": {{
        "resource_url": "exact URL if mentioned",
        "resource_type": "docs|api|tool",
        "technical_specs": {{
            "timeout": "30s",
            "version": "v1",
            "rate_limit": "100/min"
        }},
        "error_details": {{
            "error_code": "500",
            "error_message": "exact error text"
        }},
        "doc_filename": "exact filename if mentioned",
        "doc_location": "exact path if mentioned"
    }}
}}

CRITICAL:
- Only include fields that user EXPLICITLY mentioned
- Use exact values (don't approximate)
- If no URL mentioned, omit resource_url
- If no specs mentioned, omit technical_specs
"""


# ============================================
# V2 PROMPTS - REASONING EXTRACTION (LOGIC FOCUS)
# ============================================

REASONING_EXTRACTION_PROMPT_V2 = """You are extracting SEMANTIC LOGIC from AI reasoning.

Focus on INTERPRETATIONS, not raw facts:
- Context evaluation (how AI understands situation)
- Assumptions made about user/context
- Level assessment (beginner/intermediate/advanced)
- Alternatives considered (options explored)
- Decisions made (what was chosen)
- Decision rationale (WHY - explicit)
- Trade-offs (what's sacrificed for what)
- Drifts/Pivots (changes in direction)
- Implementation considerations
- Conditional plans (if X then Y)

AI Reasoning:
{reasoning}

User context (for reference):
{user_context}

Extract as JSON:
{{
    "content": "Summary of AI's reasoning process",
    "type": "reasoning",
    "certainty": "high",
    "narrative_role": "core",
    "concepts": ["decision_domain", "technical_area"],
    "block_metadata": {{
        "context_evaluation": "How AI interprets the situation",
        "assumptions": ["assumption1", "assumption2"],
        "level_assessment": "beginner|intermediate|advanced",
        "decision_choice": "What was chosen",
        "decision_reason": "WHY this choice (explicit rationale)",
        "decision_alternatives": [
            {{"option": "Alternative 1", "rejected_why": "reason"}},
            {{"option": "Alternative 2", "chosen_why": "reason"}}
        ],
        "decision_confidence": "low|medium|high",
        "trade_offs": "What's sacrificed",
        "pivot_condition": "IF X THEN Y scenarios",
        "drift_detected": "Change from previous position",
        "implementation_notes": ["consideration1", "consideration2"]
    }}
}}

CRITICAL:
- Focus on WHY and HOW, not WHAT
- Capture alternatives explicitly
- Extract pivot conditions
- Identify drifts from previous reasoning
"""


# ============================================
# V2 PROPOSITIONALIZATION PROMPTS
# ============================================

USER_PROPOSITIONALIZE_PROMPT_V2 = """Break down user's factual statements into atomic propositions.

Focus: Each proposition = one verifiable FACT

Semantic Unit:
{semantic_unit}

Return array of propositions:
[
    {{
        "su_id": "{su_id}",
        "content": "Single factual statement",
        "type": "{type}",
        "certainty": "{certainty}",
        "block_metadata": {block_metadata},
        "concepts": ["concept1", "concept2"]
    }}
]

RULES:
- 1 proposition = 1 concrete fact
- Self-contained (no pronouns without context)
- Duplicate block_metadata in each proposition
- 1-2 core concepts per proposition
- Each fact should be independently verifiable

Examples:
- "User's API endpoint is https://api.stripe.com/v1"
- "Configured timeout value is 30 seconds"
- "Current error rate measured at 5%"
"""


REASONING_PROPOSITIONALIZE_PROMPT_V2 = """Break down AI reasoning into atomic semantic units.

Focus: Each proposition = one interpretation or decision

Semantic Unit:
{semantic_unit}

Return array of propositions:
[
    {{
        "su_id": "{su_id}",
        "content": "Single reasoning step or decision",
        "type": "reasoning",
        "certainty": "{certainty}",
        "block_metadata": {block_metadata},
        "concepts": ["concept1", "concept2"]
    }}
]

RULES:
- 1 proposition = 1 reasoning step
- Include WHY explicitly
- Separate alternatives (one prop per alternative)
- Separate decision from rationale (but link them)
- Capture drifts/pivots explicitly

Examples:
- "Alternative Basic Auth rejected due to insufficient security"
- "OAuth 2.0 chosen for industry standard compliance"
- "Decision rationale: Matches user's intermediate level and REST API context"
- "Pivot condition: If failure rate exceeds 10%, recommend DLQ instead"
"""


# ============================================
# V2 EXTRACTION NODES
# ============================================

def extract_user_v2(state: dict) -> Dict:
    """
    V2 User extraction - FACTS focus
    
    Extracts:
    - Resource URLs
    - Technical specifications
    - Concrete numbers/values
    - Error details
    - File paths
    
    Does NOT interpret or add context.
    """
    start = time.time()
    
    llm = ChatAnthropic(
        model=ExtractionConfig.LLM_MODEL,
        temperature=ExtractionConfig.TEMPERATURE
    )
    
    # Get context
    context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in state.get('conversation_history', [])[-2:]
    ])
    
    prompt = USER_EXTRACTION_PROMPT_V2.format(
        user_message=state['user_message'],
        context=context or "Start of conversation"
    )
    
    try:
        response = llm.invoke(prompt)
        su = json.loads(response.content)
        su['unit_id'] = state['user_message_id']
        
        return {
            "user_semantic_unit": su,
            "stage1_user_time": time.time() - start
        }
    except Exception as e:
        return {
            "error": f"User extraction V2 error: {str(e)}",
            "stage1_user_time": time.time() - start
        }


def extract_reasoning_v2(state: dict) -> Dict:
    """
    V2 Reasoning extraction - LOGIC focus
    
    Extracts:
    - Context evaluation
    - Assumptions
    - Alternatives + why rejected/chosen
    - Decision + WHY
    - Drifts/pivots
    - Implementation considerations
    
    This REPLACES assistant message extraction from V1.
    """
    start = time.time()
    
    # If no reasoning, skip
    if not state.get('assistant_reasoning'):
        return {
            "reasoning_semantic_unit": {
                "unit_id": state['assistant_message_id'],
                "content": "No reasoning provided",
                "type": "response",
                "block_metadata": {}
            },
            "stage1_reasoning_time": time.time() - start
        }
    
    llm = ChatAnthropic(
        model=ExtractionConfig.LLM_MODEL,
        temperature=ExtractionConfig.TEMPERATURE
    )
    
    prompt = REASONING_EXTRACTION_PROMPT_V2.format(
        reasoning=state['assistant_reasoning'],
        user_context=state['user_message']
    )
    
    try:
        response = llm.invoke(prompt)
        su = json.loads(response.content)
        su['unit_id'] = state['assistant_message_id']
        su['speaker'] = 'assistant'
        
        return {
            "reasoning_semantic_unit": su,
            "stage1_reasoning_time": time.time() - start
        }
    except Exception as e:
        return {
            "error": f"Reasoning extraction V2 error: {str(e)}",
            "stage1_reasoning_time": time.time() - start
        }


def propositionalize_user_v2(state: dict) -> Dict:
    """V2 user propositionalization - FACTS to atomic props"""
    start = time.time()
    
    llm = ChatAnthropic(
        model=ExtractionConfig.LLM_MODEL,
        temperature=ExtractionConfig.TEMPERATURE
    )
    
    su = state['user_semantic_unit']
    
    prompt = USER_PROPOSITIONALIZE_PROMPT_V2.format(
        semantic_unit=json.dumps(su, ensure_ascii=False),
        su_id=su['unit_id'],
        type=su.get('type', 'statement'),
        certainty=su.get('certainty', 'medium'),
        block_metadata=su.get('block_metadata', {})
    )
    
    try:
        response = llm.invoke(prompt)
        props = json.loads(response.content)
        
        return {
            "user_propositions": props,
            "stage2_user_time": time.time() - start
        }
    except Exception as e:
        return {
            "error": f"User propositionalize V2 error: {str(e)}",
            "user_propositions": [],
            "stage2_user_time": time.time() - start
        }


def propositionalize_reasoning_v2(state: dict) -> Dict:
    """V2 reasoning propositionalization - LOGIC to atomic props"""
    start = time.time()
    
    llm = ChatAnthropic(
        model=ExtractionConfig.LLM_MODEL,
        temperature=ExtractionConfig.TEMPERATURE
    )
    
    su = state['reasoning_semantic_unit']
    
    prompt = REASONING_PROPOSITIONALIZE_PROMPT_V2.format(
        semantic_unit=json.dumps(su, ensure_ascii=False),
        su_id=su['unit_id'],
        certainty=su.get('certainty', 'high'),
        block_metadata=su.get('block_metadata', {})
    )
    
    try:
        response = llm.invoke(prompt)
        props = json.loads(response.content)
        
        return {
            "reasoning_propositions": props,
            "stage2_reasoning_time": time.time() - start
        }
    except Exception as e:
        return {
            "error": f"Reasoning propositionalize V2 error: {str(e)}",
            "reasoning_propositions": [],
            "stage2_reasoning_time": time.time() - start
        }
