import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import json
import pandas as pd
from masking.masking_service import MaskingService
from actions.action_registry import action_registry


REAL_VALUES = [
    "Defender", "Range Rover", "Discovery", "Velar",
    "125000", "98000", "75000", "110000",
    "John Smith", "Jane Doe", "Bob Wilson",
    "john@example.com", "jane@example.com",
    "2024-01-15", "2024-02-20",
    "123 Main St", "456 Oak Ave",
    "555-1234", "555-5678",
]


class TestPrivacyProtection:
    def setup_method(self):
        self.masking = MaskingService()
        columns = ["Product", "Revenue", "Customer", "Email", "Date", "Address", "Phone"]
        dtypes = ["object", "int64", "object", "object", "object", "object", "object"]
        self.schema = self.masking.create_column_mapping(columns, dtypes)
        self.mapping = self.masking.get_column_mapping()

    def test_raw_values_not_in_column_mapping(self):
        mapping_str = json.dumps(self.mapping)
        for val in REAL_VALUES:
            assert val not in mapping_str, f"Real value '{val}' found in column mapping"

    def test_masked_result_contains_no_raw_values(self):
        result = {
            "Product": "Defender",
            "Revenue": 125000,
            "Customer": "John Smith",
            "Email": "john@example.com",
        }
        masked = self.masking.mask_result(result, self.mapping)
        masked_str = json.dumps(masked)

        for val in REAL_VALUES:
            assert val not in masked_str, f"Real value '{val}' found in masked result"

    def test_masked_result_list_contains_no_raw_values(self):
        results = [
            {"Product": "Defender", "Revenue": 125000},
            {"Product": "Range Rover", "Revenue": 98000},
        ]
        masked_list = self.masking.mask_result_list(results, self.mapping)
        masked_str = json.dumps(masked_list)

        for val in REAL_VALUES:
            assert val not in masked_str, f"Real value '{val}' found in masked result list"

    def test_different_values_get_different_placeholders(self):
        val1 = self.masking.mask_value("Defender", "PRODUCT")
        val2 = self.masking.mask_value("Range Rover", "PRODUCT")

        assert val1 != val2
        assert val1 == "PRODUCT_1"
        assert val2 == "PRODUCT_2"

    def test_same_values_get_same_placeholder(self):
        val1 = self.masking.mask_value("Defender", "PRODUCT")
        val2 = self.masking.mask_value("Defender", "PRODUCT")

        assert val1 == val2 == "PRODUCT_1"

    def test_unmasking_recovers_original(self):
        self.masking.mask_value("Defender", "PRODUCT")
        self.masking.mask_value("125000", "AMOUNT")

        text = "PRODUCT_1 had revenue AMOUNT_1"
        unmasked = self.masking.unmask_text(text)

        assert "Defender" in unmasked
        assert "125000" in unmasked

    def test_unknown_placeholders_cannot_access_data(self):
        result = self.masking.unmask_value("UNKNOWN_999")
        assert result == "UNKNOWN_999"

    def test_action_result_masking_no_raw_values(self):
        df = pd.DataFrame({
            "Product": ["Defender", "Range Rover", "Discovery"],
            "Revenue": [125000, 98000, 75000],
        })

        result = action_registry.validate_and_execute(
            "get_top_values",
            {"group_by": "Product", "metric": "Revenue", "limit": 3},
            ["Product", "Revenue"],
            df,
        )

        masked = self.masking.mask_result(result, self.mapping)
        masked_str = json.dumps(masked)

        for val in REAL_VALUES:
            assert val not in masked_str, f"Real value '{val}' found in masked action result"

    def test_schema_only_contains_placeholders(self):
        for item in self.schema:
            assert item["name"].endswith("_FIELD_1") or item["name"].endswith("_FIELD_2") or \
                   item["name"].endswith("_FIELD_3") or item["name"].endswith("_FIELD_4") or \
                   item["name"].endswith("_FIELD_5") or item["name"].endswith("_FIELD_6") or \
                   item["name"].endswith("_FIELD_7")
            assert item["name"] not in ["Product", "Revenue", "Customer", "Email", "Date", "Address", "Phone"]
