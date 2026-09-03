from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAction(ABC):
    """Base class for all dataset actions."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def validate(self, params: Dict[str, Any], available_columns: List[str]) -> Optional[str]:
        """Validate parameters. Returns error message or None if valid."""
        pass

    @abstractmethod
    def execute(self, df, params: Dict[str, Any], real_column_map: Dict[str, str]) -> Any:
        """Execute action against a real Pandas DataFrame."""
        pass

    def to_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
