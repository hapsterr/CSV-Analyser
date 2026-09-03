from typing import Any, Dict, List, Optional
from .base_action import BaseAction
from .dataset_summary import DatasetSummaryAction
from .calculate_total import CalculateTotalAction
from .calculate_average import CalculateAverageAction
from .get_top_values import GetTopValuesAction
from .get_bottom_values import GetBottomValuesAction
from .get_missing_values import GetMissingValuesAction
from .get_trend import GetTrendAction


class ActionRegistry:
    """Registry of all available actions. Only registered actions can execute."""

    def __init__(self):
        self._actions: Dict[str, BaseAction] = {}

    def register(self, action: BaseAction):
        self._actions[action.name] = action

    def get(self, name: str) -> Optional[BaseAction]:
        return self._actions.get(name)

    def list_actions(self) -> List[Dict]:
        return [a.to_schema() for a in self._actions.values()]

    def list_action_names(self) -> List[str]:
        return list(self._actions.keys())

    def validate_and_execute(self, action_name: str, params: Dict[str, Any],
                             available_columns: List[str], df) -> Any:
        action = self._actions.get(action_name)
        if action is None:
            raise ValueError(f"Unknown action: {action_name}")

        error = action.validate(params, available_columns)
        if error:
            raise ValueError(error)

        return action.execute(df, params, {})


action_registry = ActionRegistry()
action_registry.register(DatasetSummaryAction())
action_registry.register(CalculateTotalAction())
action_registry.register(CalculateAverageAction())
action_registry.register(GetTopValuesAction())
action_registry.register(GetBottomValuesAction())
action_registry.register(GetMissingValuesAction())
action_registry.register(GetTrendAction())
