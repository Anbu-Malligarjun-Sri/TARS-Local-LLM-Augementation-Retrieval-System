"""
TARS Embeddings Module
Handles text embedding generation using sentence-transformers.
"""

import logging
from typing import List

try:
    import numpy as np
    from openai import OpenAI
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    np = None
    OpenAI = None

from ..utils.config import get_config


logger = logging.getLogger("tars.embeddings")


class EmbeddingGenerator:
    """Generates embeddings through LM Studio's OpenAI-compatible API."""
    
    def __init__(self, model_name: str | None = None):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers package not installed")
        
        config = get_config()
        self.model_name = model_name or config.embedding_model
        
        self.client = OpenAI(
            base_url=config.lm_studio_base_url,
            api_key="lm-studio",
        )
        self.embedding_dim = config.embedding_dimension
        logger.info("Using LM Studio embedding model: %s (%d dimensions)", self.model_name, self.embedding_dim)
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        return self.embed_query(text)

    def embed_query(self, text: str) -> List[float]:
        """Embed a retrieval query using Nomic's search-query task prefix."""
        prefix = "search_query: " if "nomic" in self.model_name.lower() else ""
        return self._embed_inputs([f"{prefix}{text}"])[0]
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            
        Returns:
            List of embeddings
        """
        return self.embed_documents(texts, batch_size=batch_size)

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed documents using Nomic's search-document task prefix."""
        prefix = "search_document: " if "nomic" in self.model_name.lower() else ""
        return self._embed_inputs(
            [f"{prefix}{text}" for text in texts],
            batch_size=batch_size,
        )

    def _embed_inputs(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts[start : start + batch_size],
            )
            batch = sorted(response.data, key=lambda item: item.index)
            embeddings.extend(item.embedding for item in batch)

        if embeddings and len(embeddings[0]) != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch: configured {self.embedding_dim}, "
                f"model returned {len(embeddings[0])}"
            )
        return embeddings
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0 to 1)
        """
        emb1 = np.array(self.embed(text1))
        emb2 = np.array(self.embed(text2))
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)


# Global embedding generator
_embedding_generator: EmbeddingGenerator | None = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create the global embedding generator."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
