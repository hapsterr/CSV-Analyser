from typing import Any, Dict, List, Optional
from .base_action import BaseAction


class DatasetSummaryAction(BaseAction):
    @property
    def name(self) -> str:
        return "dataset_summary"

    @property
    def description(self) -> str:
        return "Get a summary of the dataset including row count, column count, and column types."

    @property
    def parameters(self) -> Dict[str, str]:
        return {}

    def validate(self, params: Dict[str, Any], available_columns: List[str]) -> Optional[str]:
        return None

    def execute(self, df, params: Dict[str, Any], real_column_map: Dict[str, str]) -> Any:
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_types": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        }
