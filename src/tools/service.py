from functools import lru_cache
from src.memory.service import get_repository
from .gateway import ToolGateway
from .projects import Projects
from .calendar import LocalCalendar
from .web import PublicWeb,web_tools

@lru_cache(maxsize=1)
def get_gateway():
    repository=get_repository()
    return ToolGateway(repository,Projects(repository).tools()+LocalCalendar(repository).tools()+web_tools(PublicWeb()))
