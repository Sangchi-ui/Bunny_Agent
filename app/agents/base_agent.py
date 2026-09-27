from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    @abstractmethod
    async def send_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Sends a task/prompt to the external agent.
        Returns {"success": bool, "handle": str, "error": str}
        """
        pass

    @abstractmethod
    async def is_finished(self, handle: str) -> bool:
        """Checks whether the delegated task has completed."""
        pass

    @abstractmethod
    async def get_result(self, handle: str) -> Dict[str, Any]:
        """
        Retrieves the result once finished.
        Returns {"success": bool, "result": str, "error": str}
        """
        pass

    @abstractmethod
    def get_status_description(self, handle: str) -> str:
        """Returns a human-readable status for reporting."""
        pass
