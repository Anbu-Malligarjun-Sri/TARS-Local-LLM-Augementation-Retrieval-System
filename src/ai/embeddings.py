"""
TARS Embeddings Module
Handles text embedding generation using sentence-transformers.
"""

import logging
from typing import List

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    np = None
    SentenceTransformer = None

from ..utils.config import get_config


logger = logging.getLogger("tars.embeddings")


class EmbeddingGenerator:
    """Generates embeddings for text using sentence-transformers."""
    
    def __init__(self, model_name: str | None = None):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers package not installed")
        
        config = get_config()
        self.model_name = model_name or config.embedding_model
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            
        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings.tolist()
    
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
