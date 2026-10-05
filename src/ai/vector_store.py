"""
TARS Vector Store
ChromaDB integration for storing and retrieving knowledge embeddings.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None

from ..utils.config import get_config


logger = logging.getLogger("tars.vector_store")


class VectorStore:
    """
    Vector database using ChromaDB for storing and retrieving knowledge.
    
    Features:
    - Persistent local storage
    - Semantic search
    - Metadata filtering
    - Topic-based collections
    """
    
    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None
    ):
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb package not installed. Install with: pip install chromadb")
        
        config = get_config()
        self.persist_dir = Path(persist_dir or config.chroma_persist_dir)
        self.collection_name = collection_name or config.chroma_collection_name
        
        # Ensure persist directory exists
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        logger.info(f"Initializing ChromaDB at: {self.persist_dir}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "TARS knowledge base", "hnsw:space": "cosine"}
        )
        
        logger.info("Collection '%s' ready with %d documents", self.collection_name, self.collection.count())
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: List[float] | None = None,
        metadata: Dict[str, Any] | None = None
    ) -> None:
        """
        Add a single document to the vector store.
        
        Args:
            doc_id: Unique identifier for the document
            text: Document text
            embedding: Pre-computed embedding (optional, will use ChromaDB's default if not provided)
            metadata: Additional metadata
        """
        add_kwargs = {
            "ids": [doc_id],
            "documents": [text],
            "metadatas": [metadata or {}]
        }
        
        if embedding:
            add_kwargs["embeddings"] = [embedding]
        
        self.collection.add(**add_kwargs)
        logger.debug(f"Added document: {doc_id}")
    
    def add_documents(
        self,
        doc_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]] | None = None,
        metadatas: List[Dict[str, Any]] | None = None
    ) -> None:
        """
        Add multiple documents to the vector store.
        
        Args:
            doc_ids: List of unique identifiers
            texts: List of document texts
            embeddings: Pre-computed embeddings (optional)
            metadatas: List of metadata dictionaries
        """
        add_kwargs = {
            "ids": doc_ids,
            "documents": texts,
            "metadatas": metadatas or [{} for _ in texts]
        }
        
        if embeddings:
            add_kwargs["embeddings"] = embeddings
        
        self.collection.add(**add_kwargs)
        logger.info(f"Added {len(doc_ids)} documents")

    def existing_ids(self, doc_ids: List[str]) -> set[str]:
        """Return IDs already present in the collection."""
        if not doc_ids:
            return set()
        existing = self.collection.get(ids=doc_ids, include=[])
        return set(existing.get("ids", []))
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Dict[str, Any] | None = None,
        query_embedding: List[float] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            query_embedding: Pre-computed query embedding
            
        Returns:
            List of matching documents with scores
        """
        search_kwargs = {
            "n_results": n_results,
        }
        
        if query_embedding:
            search_kwargs["query_embeddings"] = [query_embedding]
        else:
            search_kwargs["query_texts"] = [query]
        
        if where:
            search_kwargs["where"] = where
        
        results = self.collection.query(**search_kwargs)
        
        # Format results
        formatted = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0
                })
        
        return formatted
    
    def search_by_topic(
        self,
        query: str,
        topic: str,
        n_results: int = 5,
        query_embedding: List[float] | None = None,
    ) -> List[Dict[str, Any]]:
        """Search within a specific topic."""
        return self.search(
            query,
            n_results,
            where={"topic": topic},
            query_embedding=query_embedding,
        )
    
    def get_document(self, doc_id: str) -> Dict[str, Any] | None:
        """Get a specific document by ID."""
        result = self.collection.get(ids=[doc_id])
        
        if result and result["ids"]:
            return {
                "id": result["ids"][0],
                "text": result["documents"][0] if result["documents"] else "",
                "metadata": result["metadatas"][0] if result["metadatas"] else {}
            }
        
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()
    
    def list_topics(self) -> List[str]:
        """List all unique topics in the collection."""
        # Get all metadata
        all_docs = self.collection.get()
        topics = set()
        
        if all_docs and all_docs["metadatas"]:
            for metadata in all_docs["metadatas"]:
                if metadata and "topic" in metadata:
                    topics.add(metadata["topic"])
        
        return sorted(topics)
    
    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "TARS knowledge base", "hnsw:space": "cosine"}
        )
        logger.info("Cleared all documents from collection")


# Global vector store
_vector_store: VectorStore | None = None


def get_vector_store(collection_name: str | None = None) -> VectorStore:
    """Get or create the global vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(collection_name=collection_name)
    return _vector_store
