from abc import ABC, abstractmethod

from paper_survey_agent.models.paper import Paper


class BaseScientificAPI(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        pass

    @abstractmethod
    async def get_paper_details(self, paper_id: str) -> Paper:
        pass
