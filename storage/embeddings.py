"""
Embedding generation for Living Knowledge Ecosystem

Uses OpenAI text-embedding-3-small (1536 dimensions)
for best quality validation.
"""

from openai import OpenAI
from typing import List, Union
import os


class EmbeddingGenerator:
    """Generate embeddings using OpenAI."""

    def __init__(self, api_key: str = None):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536

    def generate(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            List of 1536 floats
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (each 1536 floats)
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        # Ensure order matches input
        embeddings = [None] * len(texts)
        for data in response.data:
            embeddings[data.index] = data.embedding

        return embeddings

    def get_dimensions(self) -> int:
        """Get embedding dimensionality."""
        return self.dimensions

    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model": self.model,
            "dimensions": self.dimensions,
            "similarity_function": "cosine",
            "provider": "OpenAI"
        }


# =============================================================================
# Utility Functions
# =============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score (0-1)
    """
    import math

    # Dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Magnitudes
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    # Cosine similarity
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def format_embedding_for_neo4j(embedding: List[float]) -> List[float]:
    """
    Format embedding for Neo4j storage.

    Neo4j expects list of floats (already correct format).

    Args:
        embedding: OpenAI embedding

    Returns:
        Formatted embedding (same as input for OpenAI)
    """
    return embedding


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Test embedding generation
    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing OpenAI Embeddings...")
    print("="*70 + "\n")

    generator = EmbeddingGenerator()

    print(f"Model: {generator.model}")
    print(f"Dimensions: {generator.dimensions}\n")

    # Single text
    print("Generating embedding for single text...")
    text1 = "User întreabă ce înseamnă o unitate semantică"
    embedding1 = generator.generate(text1)

    print(f"✅ Generated embedding: {len(embedding1)} dimensions")
    print(f"   First 5 values: {embedding1[:5]}\n")

    # Batch
    print("Generating embeddings for batch...")
    texts = [
        "User întreabă ce înseamnă o unitate semantică",
        "O unitate semantică este o grupare de elemente",
        "Propoziționalizarea descompune text în afirmații atomice"
    ]

    embeddings = generator.generate_batch(texts)
    print(f"✅ Generated {len(embeddings)} embeddings\n")

    # Similarity test
    print("Testing cosine similarity...")
    sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
    sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])

    print(f"Similarity (text1 vs text2): {sim_1_2:.4f}")
    print(f"Similarity (text1 vs text3): {sim_1_3:.4f}\n")

    print("="*70)
    print("✅ Embeddings working!")
