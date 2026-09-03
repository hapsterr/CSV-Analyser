import pandas as pd
from typing import Any, Dict, List, Optional
from .base_action import BaseAction


class GetTrendAction(BaseAction):
    @property
    def name(self) -> str:
        return "get_trend"

    @property
    def description(self) -> str:
        return "Get a time-series trend of a numeric metric over a date column."

    @property
    def parameters(self) -> Dict[str, str]:
        return {"date_column": "COLUMN_NAME", "metric": "COLUMN_NAME"}

    def validate(self, params: Dict[str, Any], available_columns: List[str]) -> Optional[str]:
        if "date_column" not in params:
            return "Missing required parameter: date_column"
        if "metric" not in params:
            return "Missing required parameter: metric"
        if not isinstance(params["date_column"], str):
            return "Parameter 'date_column' must be a string"
        if not isinstance(params["metric"], str):
            return "Parameter 'metric' must be a string"
        if params["date_column"] not in available_columns:
            return f"Column '{params['date_column']}' not found in dataset"
        if params["metric"] not in available_columns:
            return f"Column '{params['metric']}' not found in dataset"
        return None

    def execute(self, df, params: Dict[str, Any], real_column_map: Dict[str, str]) -> Any:
        date_col = params["date_column"]
        metric = params["metric"]

        temp = df.copy()
        try:
            temp[date_col] = pd.to_datetime(temp[date_col])
        except Exception:
            return {"error": f"Column '{date_col}' could not be parsed as dates"}

        temp = temp.sort_values(date_col)
        trend = temp.groupby(date_col)[metric].sum().reset_index()
        trend = trend.head(100)

        results = []
        for _, row in trend.iterrows():
            date_val = str(row[date_col].date()) if hasattr(row[date_col], 'date') else str(row[date_col])
            results.append({"date": date_val, "value": float(row[metric])})

        return {"results": results, "date_column": date_col, "metric": metric}
