import pandas as pd
from typing import Any, Dict, List, Optional
from .base_action import BaseAction


class GetMissingValuesAction(BaseAction):
    @property
    def name(self) -> str:
        return "get_missing_values"

    @property
    def description(self) -> str:
        return "Count missing values in a specific column or all columns."

    @property
    def parameters(self) -> Dict[str, str]:
        return {"column": "COLUMN_NAME"}

    def validate(self, params: Dict[str, Any], available_columns: List[str]) -> Optional[str]:
        if "column" not in params:
            return "Missing required parameter: column"
        if not isinstance(params["column"], str):
            return "Parameter 'column' must be a string"
        if params["column"] not in available_columns:
            return f"Column '{params['column']}' not found in dataset"
        return None

    def execute(self, df, params: Dict[str, Any], real_column_map: Dict[str, str]) -> Any:
        col = params["column"]
        missing_count = int(df[col].isnull().sum())
        total = len(df)
        percentage = round((missing_count / total) * 100, 2) if total > 0 else 0
        return {
            "column": col,
            "missing_count": missing_count,
            "total_rows": total,
            "missing_percentage": percentage,
        }
