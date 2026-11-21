"""Configured memory service; local storage needs no model/server to start."""
from functools import lru_cache
from pathlib import Path
from src.utils.config import get_config
from .repository import Repository
from .conversations import DurableMemoryStore, import_legacy

@lru_cache(maxsize=1)
def get_repository():
    config = get_config()
    if config.memory_embeddings == 'lm_studio':
        from src.ai.embeddings import EmbeddingGenerator
        generator = EmbeddingGenerator()
        return Repository(config.memory_db_path, config.memory_database_url, lambda text: generator.embed_documents([text])[0], config.embedding_model, config.embedding_dimension, query_embedder=generator.embed_query)
    return Repository(config.memory_db_path,config.memory_database_url)

def create_store():
    config = get_config()
    repository = get_repository()
    import_legacy(repository, config.project_root / 'data' / 'conversations', Path(config.memory_db_path).parent / 'legacy-snapshots')
    return DurableMemoryStore(repository)
