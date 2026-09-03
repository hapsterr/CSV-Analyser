import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from masking.masking_service import MaskingService


class TestMaskingService:
    def setup_method(self):
        self.masking = MaskingService()

    def test_column_mapping_creation(self):
        columns = ["Product", "Revenue", "Date"]
        dtypes = ["object", "int64", "datetime64"]
        schema = self.masking.create_column_mapping(columns, dtypes)

        assert len(schema) == 3
        assert schema[0]["name"] == "TEXT_FIELD_1"
        assert schema[1]["name"] == "NUMBER_FIELD_1"
        assert schema[2]["name"] == "DATE_FIELD_1"

    def test_column_masking(self):
        self.masking.create_column_mapping(["Product", "Revenue"], ["object", "int64"])

        assert self.masking.mask_column("Product") == "TEXT_FIELD_1"
        assert self.masking.mask_column("Revenue") == "NUMBER_FIELD_1"
        assert self.masking.mask_column("Unknown") == "Unknown"

    def test_column_unmasking(self):
        self.masking.create_column_mapping(["Product", "Revenue"], ["object", "int64"])

        assert self.masking.unmask_column("TEXT_FIELD_1") == "Product"
        assert self.masking.unmask_column("NUMBER_FIELD_1") == "Revenue"
        assert self.masking.unmask_column("UNKNOWN") == "UNKNOWN"

    def test_value_masking(self):
        val1 = self.masking.mask_value("Defender", "PRODUCT")
        val2 = self.masking.mask_value("Range Rover", "PRODUCT")
        val3 = self.masking.mask_value("Defender", "PRODUCT")

        assert val1 == "PRODUCT_1"
        assert val2 == "PRODUCT_2"
        assert val3 == "PRODUCT_1"  # Same value gets same placeholder

    def test_value_unmasking(self):
        self.masking.mask_value("Defender", "PRODUCT")
        self.masking.mask_value("125000", "AMOUNT")

        assert self.masking.unmask_value("PRODUCT_1") == "Defender"
        assert self.masking.unmask_value("AMOUNT_1") == "125000"
        assert self.masking.unmask_value("UNKNOWN") == "UNKNOWN"

    def test_result_masking(self):
        self.masking.create_column_mapping(["Product", "Revenue"], ["object", "int64"])
        result = {"Product": "Defender", "Revenue": 125000}
        masked = self.masking.mask_result(result, self.masking.get_column_mapping())

        assert "TEXT_FIELD_1" in masked
        assert "NUMBER_FIELD_1" in masked
        assert masked["TEXT_FIELD_1"] != "Defender"
        assert masked["NUMBER_FIELD_1"] != "125000"

    def test_text_unmasking(self):
        self.masking.create_column_mapping(["Product", "Revenue"], ["object", "int64"])
        self.masking.mask_value("Defender", "PRODUCT")
        self.masking.mask_value("125000", "AMOUNT")

        text = "TEXT_FIELD_1 generated PRODUCT_1 and NUMBER_FIELD_1 was AMOUNT_1"
        unmasked = self.masking.unmask_text(text)

        assert "Product" in unmasked
        assert "Defender" in unmasked
        assert "125000" in unmasked
        assert "TEXT_FIELD_1" not in unmasked
        assert "PRODUCT_1" not in unmasked
        assert "AMOUNT_1" not in unmasked

    def test_no_raw_data_in_masked_result(self):
        self.masking.create_column_mapping(["Customer", "Email", "Phone"], ["object", "object", "object"])
        result = {"Customer": "John Smith", "Email": "john@example.com", "Phone": "555-1234"}
        masked = self.masking.mask_result(result, self.masking.get_column_mapping())

        for val in masked.values():
            assert val != "John Smith"
            assert val != "john@example.com"
            assert val != "555-1234"
