"""
DSPy-based proposition extraction for semantic memory systems.

Compares:
1. Baseline: Direct LLM prompting
2. DSPy: Optimized signatures with few-shot examples
"""

import dspy
from typing import List, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class Proposition:
    """Atomic, self-contained factual statement."""
    content: str
    type: str  # fact, opinion, decision, question, etc.
    certainty: str  # high, medium, low
    concepts: List[str]
    source_role: str  # user or assistant


# ============================================================================
# DSPy Signatures
# ============================================================================

class ExtractPropositions(dspy.Signature):
    """Extract atomic, self-contained propositions from a conversational message.

    Each proposition must:
    - Express ONE fact, opinion, or statement
    - Be independently understandable (resolve all references like 'ea', 'asta')
    - Be verifiable or falsifiable
    - Preserve the original semantic intent

    For short responses like 'Da' or 'Exact', expand with implicit context.
    For technical explanations, break into atomic knowledge units.
    """

    message_content: str = dspy.InputField(desc="The message to extract propositions from")
    conversation_context: str = dspy.InputField(desc="Previous messages for resolving references")
    role: str = dspy.InputField(desc="Speaker role: user or assistant")

    propositions: List[Dict[str, Any]] = dspy.OutputField(
        desc="""List of propositions in JSON format:
        [
          {
            "content": "Self-contained atomic statement",
            "type": "fact|opinion|decision|question|agreement",
            "certainty": "high|medium|low",
            "concepts": ["key", "concepts"]
          }
        ]"""
    )


class SemanticUnitSummarizer(dspy.Signature):
    """Create a high-level semantic unit summary for narrative structure.

    This is NOT for embeddings - it's metadata for conversation flow understanding.
    """

    message_content: str = dspy.InputField()
    role: str = dspy.InputField()

    summary: str = dspy.OutputField(desc="Concise description of the message's role in conversation")
    narrative_role: str = dspy.OutputField(desc="core|supportive|peripheral")
    main_concepts: List[str] = dspy.OutputField(desc="Key concepts discussed")


# ============================================================================
# DSPy Modules
# ============================================================================

class PropositionExtractor(dspy.Module):
    """Extract propositions using DSPy with optimized prompting."""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractPropositions)

    def forward(self, message_content: str, conversation_context: str, role: str):
        result = self.extract(
            message_content=message_content,
            conversation_context=conversation_context,
            role=role
        )

        # Parse JSON output
        try:
            if isinstance(result.propositions, str):
                propositions = json.loads(result.propositions)
            else:
                propositions = result.propositions

            return [
                Proposition(
                    content=p["content"],
                    type=p.get("type", "fact"),
                    certainty=p.get("certainty", "medium"),
                    concepts=p.get("concepts", []),
                    source_role=role
                )
                for p in propositions
            ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing propositions: {e}")
            print(f"Raw output: {result.propositions}")
            return []


class DualLayerProcessor(dspy.Module):
    """
    Processes messages into two layers:
    1. Semantic units - for narrative structure (NOT embedded)
    2. Propositions - for embeddings and retrieval
    """

    def __init__(self):
        super().__init__()
        self.proposition_extractor = PropositionExtractor()
        self.semantic_summarizer = dspy.ChainOfThought(SemanticUnitSummarizer)

    def forward(self, message_content: str, conversation_context: str, role: str):
        # Extract propositions for embeddings
        propositions = self.proposition_extractor.forward(
            message_content=message_content,
            conversation_context=conversation_context,
            role=role
        )

        # Create semantic unit for narrative
        semantic_unit = self.semantic_summarizer(
            message_content=message_content,
            role=role
        )

        return {
            "semantic_unit": {
                "summary": semantic_unit.summary,
                "narrative_role": semantic_unit.narrative_role,
                "main_concepts": semantic_unit.main_concepts
            },
            "propositions": propositions
        }


# ============================================================================
# Baseline: Direct Prompting (for comparison)
# ============================================================================

class BaselinePropositionExtractor:
    """Traditional prompt-based extraction without DSPy optimization."""

    def __init__(self, lm):
        self.lm = lm

    def extract(self, message_content: str, conversation_context: str, role: str) -> List[Proposition]:
        prompt = f"""Extract atomic, self-contained propositions from this message.

Conversation context:
{conversation_context}

Current message ({role}):
{message_content}

Rules:
- Each proposition = ONE fact/opinion/statement
- Resolve all references (ea → name, asta → specific concept)
- Make each proposition independently understandable
- For short responses like "Da", expand with implicit context

Return JSON:
[
  {{
    "content": "atomic statement",
    "type": "fact|opinion|decision|agreement",
    "certainty": "high|medium|low",
    "concepts": ["key", "concepts"]
  }}
]
"""

        response = self.lm(prompt)

        try:
            # DSPy LM returns list with single string
            if isinstance(response, list) and len(response) > 0:
                response_text = response[0]
            elif isinstance(response, str):
                response_text = response
            elif hasattr(response, 'choices'):
                response_text = response.choices[0].message.content
            else:
                response_text = str(response)

            # Strip markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Parse JSON
            propositions = json.loads(response_text)

            return [
                Proposition(
                    content=p["content"],
                    type=p.get("type", "fact"),
                    certainty=p.get("certainty", "medium"),
                    concepts=p.get("concepts", []),
                    source_role=role
                )
                for p in propositions
            ]
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            print(f"Baseline parsing error: {e}")
            print(f"Response was: {response}")
            return []


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Configure DSPy with your LLM
    lm = dspy.LM(model="openai/gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)

    # Example message
    message = """Absolut! Propoziționalizarea rezolvă probleme fundamentale în RAG și embeddings:

**Pentru embeddings:**
- **Densitate semantică** - fiecare embedding captează UN concept clar, nu multiple idei amestecate
- **Similaritate mai precisă** - query-ul "Cine a predat matematică?" se potrivește direct cu "Maria este profesoară de matematică"
"""

    context = "User asked about propositionalization and embeddings."

    # DSPy approach
    processor = DualLayerProcessor()
    result = processor.forward(message, context, "assistant")

    print("=== SEMANTIC UNIT (for narrative) ===")
    print(json.dumps(result["semantic_unit"], indent=2, ensure_ascii=False))

    print("\n=== PROPOSITIONS (for embeddings) ===")
    for prop in result["propositions"]:
        print(f"- [{prop.type}] {prop.content}")
        print(f"  Concepts: {', '.join(prop.concepts)}")
        print()
