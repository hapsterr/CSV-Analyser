import pandas as pd
from typing import Any, Dict, List, Optional
from .base_action import BaseAction


class GetBottomValuesAction(BaseAction):
    @property
    def name(self) -> str:
        return "get_bottom_values"

    @property
    def description(self) -> str:
        return "Find the lowest-performing values grouped by a categorical field."

    @property
    def parameters(self) -> Dict[str, str]:
        return {"group_by": "COLUMN_NAME", "metric": "COLUMN_NAME", "limit": "NUMBER"}

    def validate(self, params: Dict[str, Any], available_columns: List[str]) -> Optional[str]:
        if "group_by" not in params:
            return "Missing required parameter: group_by"
        if "metric" not in params:
            return "Missing required parameter: metric"
        if "limit" not in params:
            return "Missing required parameter: limit"
        if not isinstance(params["group_by"], str):
            return "Parameter 'group_by' must be a string"
        if not isinstance(params["metric"], str):
            return "Parameter 'metric' must be a string"
        if not isinstance(params["limit"], int) or params["limit"] < 1:
            return "Parameter 'limit' must be a positive integer"
        if params["group_by"] not in available_columns:
            return f"Column '{params['group_by']}' not found in dataset"
        if params["metric"] not in available_columns:
            return f"Column '{params['metric']}' not found in dataset"
        return None

    def execute(self, df, params: Dict[str, Any], real_column_map: Dict[str, str]) -> Any:
        group_by = params["group_by"]
        metric = params["metric"]
        limit = min(params["limit"], 50)

        grouped = df.groupby(group_by)[metric].sum().sort_values(ascending=True).head(limit)
        results = [{"group": str(idx), "value": float(val)} for idx, val in grouped.items()]
        return {"results": results, "group_by": group_by, "metric": metric}
