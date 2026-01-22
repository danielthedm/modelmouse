from typing import Optional
import numpy as np
from openai import OpenAI


EMBEDDING_MODEL = "text-embedding-3-small"


def _cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def calculate_semantic_similarity(
    expected: str,
    actual: str,
    api_key: str
) -> Optional[float]:
    """
    Calculate 0-100 similarity score between two texts using OpenAI embeddings.

    Args:
        expected: The reference/expected text
        actual: The actual output text to compare
        api_key: OpenAI API key

    Returns:
        Float 0-100 similarity score, or None if embeddings couldn't be generated
    """
    if not api_key:
        return None

    if not expected or not actual:
        return None

    try:
        client = OpenAI(api_key=api_key)

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[expected, actual]
        )

        expected_embedding = response.data[0].embedding
        actual_embedding = response.data[1].embedding

        similarity = _cosine_similarity(expected_embedding, actual_embedding)

        score = max(0.0, min(100.0, similarity * 100))

        return round(score, 2)

    except Exception as e:
        print(f"Error calculating semantic similarity: {e}")
        return None


def calculate_batch_similarities(
    pairs: list[tuple[str, str]],
    api_key: str
) -> list[Optional[float]]:
    """
    Calculate semantic similarity for multiple text pairs efficiently.

    Args:
        pairs: List of (expected, actual) text pairs
        api_key: OpenAI API key

    Returns:
        List of similarity scores (0-100 or None for each pair)
    """
    if not api_key:
        return [None] * len(pairs)

    if not pairs:
        return []

    try:
        client = OpenAI(api_key=api_key)

        all_texts = []
        for expected, actual in pairs:
            all_texts.append(expected or "")
            all_texts.append(actual or "")

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=all_texts
        )

        results = []
        for i in range(len(pairs)):
            expected, actual = pairs[i]
            if not expected or not actual:
                results.append(None)
                continue

            expected_embedding = response.data[i * 2].embedding
            actual_embedding = response.data[i * 2 + 1].embedding

            similarity = _cosine_similarity(expected_embedding, actual_embedding)
            score = max(0.0, min(100.0, similarity * 100))
            results.append(round(score, 2))

        return results

    except Exception as e:
        print(f"Error in batch similarity: {e}")
        return [None] * len(pairs)
