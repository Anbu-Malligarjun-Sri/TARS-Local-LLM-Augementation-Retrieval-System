"""
TARS RAG System
Retrieval-Augmented Generation for knowledge-enhanced responses.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import hashlib

from .embeddings import EmbeddingGenerator, get_embedding_generator, EMBEDDINGS_AVAILABLE
from .vector_store import VectorStore, get_vector_store, CHROMA_AVAILABLE
from ..utils.config import get_config


logger = logging.getLogger("tars.rag")


class DatasetLoader:
    """Loads Q&A datasets from YAML files."""
    
    @staticmethod
    def load_yaml(file_path: Path) -> List[Dict[str, Any]]:
        """Load a YAML dataset file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        entries = []
        
        # Handle different YAML structures
        if isinstance(data, dict):
            # Look for seed_examples or similar
            if "seed_examples" in data:
                examples = data["seed_examples"]
            elif "examples" in data:
                examples = data["examples"]
            else:
                examples = []
            
            for i, example in enumerate(examples):
                entry = {
                    "id": f"{file_path.stem}_{i}",
                    "question": example.get("question", "").strip(),
                    "answer": example.get("answer", "").strip(),
                    "context": example.get("context", "").strip(),
                    "source": file_path.name
                }
                
                # Extract topic from filename
                if "relativity" in file_path.stem.lower():
                    entry["topic"] = "relativity"
                elif "qm" in file_path.stem.lower() or "quantum" in file_path.stem.lower():
                    entry["topic"] = "quantum_mechanics"
                elif "black_hole" in file_path.stem.lower():
                    entry["topic"] = "black_holes"
                elif "thermo" in file_path.stem.lower():
                    entry["topic"] = "thermodynamics"
                elif "entropy" in file_path.stem.lower():
                    entry["topic"] = "entropy"
                elif "cosmology" in file_path.stem.lower():
                    entry["topic"] = "cosmology"
                elif "big_bang" in file_path.stem.lower():
                    entry["topic"] = "big_bang"
                elif "astrobiology" in file_path.stem.lower():
                    entry["topic"] = "astrobiology"
                elif "philosophy" in file_path.stem.lower():
                    entry["topic"] = "philosophy"
                elif "mathematics" in file_path.stem.lower():
                    entry["topic"] = "mathematics"
                elif "history" in file_path.stem.lower():
                    entry["topic"] = "history_of_physics"
                elif "gravitational" in file_path.stem.lower():
                    entry["topic"] = "gravitational_physics"
                elif "ethics" in file_path.stem.lower() or "spacecraft" in file_path.stem.lower():
                    entry["topic"] = "ai_ethics"
                else:
                    entry["topic"] = "general"
                
                if entry["question"] or entry["answer"]:
                    entries.append(entry)
        
        return entries
    
    @staticmethod
    def load_directory(directory: Path) -> List[Dict[str, Any]]:
        """Load all YAML files from a directory."""
        all_entries = []
        
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return all_entries
        
        for yaml_file in directory.glob("**/*.yaml"):
            try:
                entries = DatasetLoader.load_yaml(yaml_file)
                all_entries.extend(entries)
                logger.info(f"Loaded {len(entries)} entries from {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        
        return all_entries


class RAGSystem:
    """
    Retrieval-Augmented Generation system for TARS.
    
    Uses ChromaDB for vector storage and sentence-transformers for embeddings.
    Loads knowledge from YAML Q&A datasets.
    """
    
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
        auto_load_datasets: bool = True
    ):
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb not installed")
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers not installed")
        
        self.config = get_config()
        self.vector_store = vector_store or get_vector_store()
        self.embeddings = embedding_generator or get_embedding_generator()
        self.dataset_loader = DatasetLoader()
        
        self._loaded_datasets: set[str] = set()
        
        if auto_load_datasets:
            self._load_default_datasets()
    
    def _load_default_datasets(self) -> None:
        """Load datasets from the default location."""
        datasets_dir = self.config.project_root / "Datasets Questions and Answers of TARS"
        
        if datasets_dir.exists():
            self.index_directory(datasets_dir)
        else:
            logger.warning(f"Default datasets directory not found: {datasets_dir}")
    
    def index_directory(self, directory: Path) -> int:
        """
        Index all YAML datasets in a directory.
        
        Args:
            directory: Directory containing YAML files
            
        Returns:
            Number of documents indexed
        """
        entries = self.dataset_loader.load_directory(directory)
        
        if not entries:
            return 0
        
        # Skip documents persisted by earlier processes as well as this one.
        candidate_ids = []
        for entry in entries:
            content_hash = hashlib.md5(
                (entry["question"] + entry["answer"]).encode()
            ).hexdigest()[:12]
            candidate_ids.append(f"{entry['id']}_{content_hash}")
        existing_ids = self.vector_store.existing_ids(candidate_ids)

        # Prepare documents for indexing
        doc_ids = []
        texts = []
        metadatas = []
        
        for entry in entries:
            # Create a unique ID based on content
            content_hash = hashlib.md5(
                (entry["question"] + entry["answer"]).encode()
            ).hexdigest()[:12]
            doc_id = f"{entry['id']}_{content_hash}"
            
            if doc_id in existing_ids or doc_id in self._loaded_datasets:
                continue
            
            # Combine question and answer for embedding
            text = f"Question: {entry['question']}\n\nAnswer: {entry['answer']}"
            if entry.get("context"):
                text = f"Context: {entry['context']}\n\n{text}"
            
            doc_ids.append(doc_id)
            texts.append(text)
            metadatas.append({
                "question": entry["question"][:500],  # Truncate for metadata
                "topic": entry.get("topic", "general"),
                "source": entry.get("source", "unknown")
            })
            
        
        if not doc_ids:
            logger.info("All documents already indexed")
            return 0
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embeddings.embed_documents(texts)
        
        # Add to vector store
        self.vector_store.add_documents(doc_ids, texts, embeddings, metadatas)
        self._loaded_datasets.update(doc_ids)
        
        logger.info(f"Indexed {len(doc_ids)} new documents")
        return len(doc_ids)
    
    def retrieve(
        self,
        query: str,
        n_results: int = 3,
        topic: str | None = None,
        min_relevance: float = 0.3
    ) -> str:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            n_results: Number of results to retrieve
            topic: Optional topic filter
            min_relevance: Minimum relevance score (0-1, where 1 is most similar)
            
        Returns:
            Formatted context string for augmenting LLM prompt
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed(query)
        
        # Search
        if topic:
            results = self.vector_store.search_by_topic(
                query, topic, n_results, query_embedding=query_embedding
            )
        else:
            results = self.vector_store.search(
                query,
                n_results=n_results,
                query_embedding=query_embedding
            )
        
        if not results:
            return ""
        
        # Chroma's cosine distance is 1 - cosine similarity.
        relevant_results = []
        for result in results:
            similarity = 1.0 - result["distance"]
            if similarity >= min_relevance:
                relevant_results.append(result)
        
        if not relevant_results:
            return ""
        
        # Format context
        context_parts = []
        for i, result in enumerate(relevant_results, 1):
            topic_label = result["metadata"].get("topic", "general")
            context_parts.append(
                f"[Reference {i} - {topic_label}]\n{result['text']}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        return context
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return {
            "total_documents": self.vector_store.count(),
            "loaded_datasets": len(self._loaded_datasets),
            "topics": self.vector_store.list_topics(),
            "embedding_model": self.embeddings.model_name,
            "embedding_dimension": self.embeddings.embedding_dim
        }
    
    def clear_index(self) -> None:
        """Clear all indexed documents."""
        self.vector_store.clear()
        self._loaded_datasets.clear()
        logger.info("Cleared all indexed documents")


# Global RAG system
_rag_system: RAGSystem | None = None


def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system."""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system


def is_rag_available() -> bool:
    """Check if RAG system dependencies are available."""
    return CHROMA_AVAILABLE and EMBEDDINGS_AVAILABLE
