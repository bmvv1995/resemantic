"""
Comparison test: Baseline prompting vs DSPy for proposition extraction.

Evaluates:
1. Proposition quality (atomicity, self-containment)
2. Embedding effectiveness (semantic matching)
3. Retrieval accuracy
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import dspy
from dspy_propositions import PropositionExtractor, BaselinePropositionExtractor, Proposition


class PropositionEvaluator:
    """Evaluates proposition extraction quality for embeddings."""

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(embedding_model)

    def load_conversation(self, filepath: str) -> List[Dict]:
        """Load test conversation."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['conversation']

    def build_context(self, messages: List[Dict], current_idx: int, window: int = 3) -> str:
        """Build conversation context for current message."""
        start = max(0, current_idx - window)
        context_msgs = messages[start:current_idx]

        return "\n".join([
            f"{msg['role']}: {msg['content'][:200]}..."
            for msg in context_msgs
        ])

    def extract_with_baseline(self, messages: List[Dict], lm) -> Dict[int, List[Proposition]]:
        """Extract propositions using baseline prompting."""
        extractor = BaselinePropositionExtractor(lm)
        results = {}

        for idx, msg in enumerate(messages):
            context = self.build_context(messages, idx)
            propositions = extractor.extract(
                message_content=msg['content'],
                conversation_context=context,
                role=msg['role']
            )
            results[idx] = propositions

        return results

    def extract_with_dspy(self, messages: List[Dict]) -> Dict[int, List[Proposition]]:
        """Extract propositions using DSPy."""
        extractor = PropositionExtractor()
        results = {}

        for idx, msg in enumerate(messages):
            context = self.build_context(messages, idx)
            propositions = extractor.forward(
                message_content=msg['content'],
                conversation_context=context,
                role=msg['role']
            )
            results[idx] = propositions

        return results

    def compute_embeddings(self, propositions: List[Proposition]) -> np.ndarray:
        """Compute embeddings for propositions."""
        texts = [p.content for p in propositions]
        return self.encoder.encode(texts, convert_to_numpy=True)

    def test_retrieval(
        self,
        propositions: List[Proposition],
        queries: List[str]
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Test retrieval accuracy with sample queries."""

        # Embed propositions
        prop_embeddings = self.compute_embeddings(propositions)

        # Embed queries
        query_embeddings = self.encoder.encode(queries, convert_to_numpy=True)

        results = {}
        for query, query_emb in zip(queries, query_embeddings):
            # Compute similarities
            similarities = cosine_similarity([query_emb], prop_embeddings)[0]

            # Get top 3 matches
            top_indices = np.argsort(similarities)[-3:][::-1]
            top_matches = [
                (propositions[idx].content, similarities[idx])
                for idx in top_indices
            ]

            results[query] = top_matches

        return results

    def analyze_propositions(self, propositions: List[Proposition]) -> Dict:
        """Analyze proposition characteristics."""
        return {
            "total_count": len(propositions),
            "avg_length": np.mean([len(p.content.split()) for p in propositions]),
            "type_distribution": self._count_types(propositions),
            "certainty_distribution": self._count_certainty(propositions),
            "concepts_per_proposition": np.mean([len(p.concepts) for p in propositions])
        }

    def _count_types(self, propositions: List[Proposition]) -> Dict[str, int]:
        types = {}
        for p in propositions:
            types[p.type] = types.get(p.type, 0) + 1
        return types

    def _count_certainty(self, propositions: List[Proposition]) -> Dict[str, int]:
        certainty = {}
        for p in propositions:
            certainty[p.certainty] = certainty.get(p.certainty, 0) + 1
        return certainty


def run_comparison(conversation_file: str, api_key: str):
    """Run full comparison between baseline and DSPy."""

    # Setup
    print("🔧 Setting up models...")
    lm = dspy.LM(model="openai/gpt-4o-mini", api_key=api_key, max_tokens=2000)
    dspy.configure(lm=lm)

    evaluator = PropositionEvaluator()

    # Load conversation
    print(f"📖 Loading conversation from {conversation_file}...")
    messages = evaluator.load_conversation(conversation_file)
    print(f"   Found {len(messages)} messages\n")

    # Test queries
    test_queries = [
        "Ce este o unitate semantică?",
        "De ce spaCy nu funcționează bine pentru embeddings?",
        "Care sunt beneficiile propoziționalizării?",
        "Cum ajută propoziționalizarea la RAG?",
        "Ce probleme rezolvă în embeddings?"
    ]

    # ========================================================================
    # BASELINE EXTRACTION
    # ========================================================================
    print("=" * 70)
    print("🔵 BASELINE: Direct Prompting")
    print("=" * 70)

    baseline_results = evaluator.extract_with_baseline(messages, lm)
    baseline_all_props = [p for props in baseline_results.values() for p in props]

    print(f"\n📊 Extracted {len(baseline_all_props)} propositions")
    baseline_analysis = evaluator.analyze_propositions(baseline_all_props)
    print(json.dumps(baseline_analysis, indent=2, ensure_ascii=False))

    print("\n🔍 Sample propositions:")
    for i, prop in enumerate(baseline_all_props[:5], 1):
        print(f"{i}. [{prop.type}] {prop.content}")

    print("\n🎯 Retrieval test:")
    baseline_retrieval = evaluator.test_retrieval(baseline_all_props, test_queries)
    for query, matches in list(baseline_retrieval.items())[:2]:
        print(f"\nQuery: '{query}'")
        for content, score in matches:
            print(f"  {score:.3f} | {content[:80]}...")

    # ========================================================================
    # DSPY EXTRACTION
    # ========================================================================
    print("\n" + "=" * 70)
    print("🟢 DSPY: Optimized Signatures")
    print("=" * 70)

    dspy_results = evaluator.extract_with_dspy(messages)
    dspy_all_props = [p for props in dspy_results.values() for p in props]

    print(f"\n📊 Extracted {len(dspy_all_props)} propositions")
    dspy_analysis = evaluator.analyze_propositions(dspy_all_props)
    print(json.dumps(dspy_analysis, indent=2, ensure_ascii=False))

    print("\n🔍 Sample propositions:")
    for i, prop in enumerate(dspy_all_props[:5], 1):
        print(f"{i}. [{prop.type}] {prop.content}")

    print("\n🎯 Retrieval test:")
    dspy_retrieval = evaluator.test_retrieval(dspy_all_props, test_queries)
    for query, matches in list(dspy_retrieval.items())[:2]:
        print(f"\nQuery: '{query}'")
        for content, score in matches:
            print(f"  {score:.3f} | {content[:80]}...")

    # ========================================================================
    # COMPARISON
    # ========================================================================
    print("\n" + "=" * 70)
    print("📊 COMPARISON SUMMARY")
    print("=" * 70)

    print(f"""
Metric                          Baseline        DSPy
{'─' * 60}
Total propositions              {len(baseline_all_props):<15} {len(dspy_all_props)}
Avg proposition length (words)  {baseline_analysis['avg_length']:<15.1f} {dspy_analysis['avg_length']:.1f}
Concepts per proposition        {baseline_analysis['concepts_per_proposition']:<15.1f} {dspy_analysis['concepts_per_proposition']:.1f}
""")

    # Compare retrieval scores
    print("\n🎯 Retrieval Score Comparison (average top-1 score):")
    baseline_scores = [matches[0][1] for matches in baseline_retrieval.values()]
    dspy_scores = [matches[0][1] for matches in dspy_retrieval.values()]

    print(f"Baseline avg: {np.mean(baseline_scores):.3f}")
    print(f"DSPy avg:     {np.mean(dspy_scores):.3f}")
    print(f"Improvement:  {((np.mean(dspy_scores) - np.mean(baseline_scores)) / np.mean(baseline_scores) * 100):.1f}%")

    # Save detailed results
    output = {
        "baseline": {
            "propositions": [
                {"content": p.content, "type": p.type, "concepts": p.concepts}
                for p in baseline_all_props
            ],
            "analysis": baseline_analysis,
            "retrieval_scores": {q: [(m[0], float(m[1])) for m in matches]
                                for q, matches in baseline_retrieval.items()}
        },
        "dspy": {
            "propositions": [
                {"content": p.content, "type": p.type, "concepts": p.concepts}
                for p in dspy_all_props
            ],
            "analysis": dspy_analysis,
            "retrieval_scores": {q: [(m[0], float(m[1])) for m in matches]
                                for q, matches in dspy_retrieval.items()}
        }
    }

    with open('/opt/resemantic/comparison_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n✅ Detailed results saved to comparison_results.json")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Please set OPENAI_API_KEY in .env file")
        exit(1)

    run_comparison(
        conversation_file="/opt/resemantic/test_conversation.json",
        api_key=api_key
    )
