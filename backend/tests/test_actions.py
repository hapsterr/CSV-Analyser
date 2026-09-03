import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from actions.action_registry import action_registry


class TestActionRegistry:
    def test_all_actions_registered(self):
        names = action_registry.list_action_names()
        assert "dataset_summary" in names
        assert "calculate_total" in names
        assert "calculate_average" in names
        assert "get_top_values" in names
        assert "get_bottom_values" in names
        assert "get_missing_values" in names
        assert "get_trend" in names

    def test_unknown_action_rejected(self):
        with pytest.raises(ValueError, match="Unknown action"):
            action_registry.validate_and_execute("fake_action", {}, [], None)

    def test_dataset_summary(self):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = action_registry.validate_and_execute("dataset_summary", {}, ["A", "B"], df)
        assert result["rows"] == 2
        assert result["columns"] == 2

    def test_calculate_total(self):
        df = pd.DataFrame({"Revenue": [100, 200, 300]})
        result = action_registry.validate_and_execute("calculate_total", {"column": "Revenue"}, ["Revenue"], df)
        assert result["total"] == 600

    def test_calculate_average(self):
        df = pd.DataFrame({"Revenue": [100, 200, 300]})
        result = action_registry.validate_and_execute("calculate_average", {"column": "Revenue"}, ["Revenue"], df)
        assert result["average"] == 200

    def test_get_top_values(self):
        df = pd.DataFrame({
            "Product": ["A", "B", "A", "B"],
            "Revenue": [100, 200, 150, 250]
        })
        result = action_registry.validate_and_execute(
            "get_top_values",
            {"group_by": "Product", "metric": "Revenue", "limit": 2},
            ["Product", "Revenue"],
            df,
        )
        assert len(result["results"]) == 2
        assert result["results"][0]["group"] == "B"

    def test_get_bottom_values(self):
        df = pd.DataFrame({
            "Product": ["A", "B", "A", "B"],
            "Revenue": [100, 200, 150, 250]
        })
        result = action_registry.validate_and_execute(
            "get_bottom_values",
            {"group_by": "Product", "metric": "Revenue", "limit": 2},
            ["Product", "Revenue"],
            df,
        )
        assert len(result["results"]) == 2
        assert result["results"][0]["group"] == "A"

    def test_get_missing_values(self):
        df = pd.DataFrame({"A": [1, None, 3]})
        result = action_registry.validate_and_execute(
            "get_missing_values", {"column": "A"}, ["A"], df
        )
        assert result["missing_count"] == 1
        assert result["total_rows"] == 3

    def test_parameter_validation_missing(self):
        with pytest.raises(ValueError, match="Missing"):
            action_registry.validate_and_execute("calculate_total", {}, ["Revenue"], None)

    def test_parameter_validation_invalid_column(self):
        with pytest.raises(ValueError, match="not found"):
            action_registry.validate_and_execute(
                "calculate_total", {"column": "NonExistent"}, ["Revenue"], None
            )
