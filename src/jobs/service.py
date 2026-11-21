from functools import lru_cache
from src.memory.service import get_repository
from src.utils.config import get_config
from .store import JobStore

@lru_cache(maxsize=1)
def get_store():
    config=get_config()
    return JobStore(get_repository(),config.project_root/'.runtime'/'coding'/'jobs',config.coding_repositories or {'tars':str(config.project_root)},config.coding_allow_cloud)
