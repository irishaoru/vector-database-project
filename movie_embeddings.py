"""The active movie embedding model: local Nomic Embed Text v1.5.

The previous implementation is retained in legacy_jina_embeddings.py for comparison.
"""

from nomic_embeddings import (
    CACHE, MAX_TOKENS, MODEL, REVISION, ROOT,
    NomicEmbeddingFunction as MovieEmbeddingFunction,
)
