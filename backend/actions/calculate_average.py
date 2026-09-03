import pandas as pd
from typing import Any, Dict, List, Optional
from .base_action import BaseAction


class CalculateAverageAction(BaseAction):
    @property
    def name(self) -> str:
        return "calculate_average"

    @property
    def description(self) -> str:
        return "Calculate the average (mean) of a numeric column."

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
        average = df[col].mean()
        return {"average": float(average), "column": col}
