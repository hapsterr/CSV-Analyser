from typing import Dict, List, Tuple
from collections import OrderedDict


class MaskingService:
    """Server-side masking service. Never exposes real values to AI."""

    def __init__(self):
        self._column_map: Dict[str, str] = {}
        self._reverse_column_map: Dict[str, str] = {}
        self._value_maps: Dict[str, OrderedDict] = {}
        self._reverse_value_maps: Dict[str, Dict[str, str]] = {}
        self._counters: Dict[str, int] = {}

    def _get_prefix(self, dtype) -> str:
        dtype_str = str(dtype).lower()
        if "int" in dtype_str or "float" in dtype_str:
            return "NUMBER"
        if "date" in dtype_str or "time" in dtype_str:
            return "DATE"
        if "bool" in dtype_str:
            return "BOOL"
        return "TEXT"

    def _get_counter(self, prefix: str) -> int:
        if prefix not in self._counters:
            self._counters[prefix] = 0
        self._counters[prefix] += 1
        return self._counters[prefix]

    def create_column_mapping(self, columns: List[str], dtypes) -> List[Dict]:
        schema = []
        for col, dtype in zip(columns, dtypes):
            prefix = self._get_prefix(dtype)
            idx = self._get_counter(prefix)
            placeholder = f"{prefix}_FIELD_{idx}"
            self._column_map[col] = placeholder
            self._reverse_column_map[placeholder] = col
            schema.append({"name": placeholder, "type": prefix.lower()})
        return schema

    def mask_column(self, real_name: str) -> str:
        return self._column_map.get(real_name, real_name)

    def unmask_column(self, placeholder: str) -> str:
        return self._reverse_column_map.get(placeholder, placeholder)

    def mask_value(self, real_value, value_prefix: str = "VALUE") -> str:
        str_val = str(real_value)
        prefix = value_prefix.upper()
        if prefix not in self._value_maps:
            self._value_maps[prefix] = OrderedDict()
            self._reverse_value_maps[prefix] = {}

        if str_val in self._value_maps[prefix]:
            return self._value_maps[prefix][str_val]

        idx = len(self._value_maps[prefix]) + 1
        placeholder = f"{prefix}_{idx}"
        self._value_maps[prefix][str_val] = placeholder
        self._reverse_value_maps[prefix][placeholder] = str_val
        return placeholder

    def unmask_value(self, placeholder: str) -> str:
        for prefix, rev_map in self._reverse_value_maps.items():
            if placeholder in rev_map:
                return rev_map[placeholder]
        return placeholder

    def _mask_value_for_result(self, value):
        if isinstance(value, (int, float)):
            return self.mask_value(value, "AMOUNT")
        elif isinstance(value, str):
            if any(c.isdigit() for c in value) and len(value) >= 4:
                return self.mask_value(value, "VALUE")
            else:
                return self.mask_value(value, "ITEM")
        return str(value)

    def mask_result(self, result: dict, column_mapping: Dict[str, str]) -> dict:
        masked = {}
        for key, value in result.items():
            placeholder = column_mapping.get(key, key)
            if isinstance(value, list):
                masked_list = []
                for item in value:
                    if isinstance(item, dict):
                        masked_item = {}
                        for k, v in item.items():
                            k_placeholder = column_mapping.get(k, k)
                            masked_item[k_placeholder] = self._mask_value_for_result(v)
                        masked_list.append(masked_item)
                    else:
                        masked_list.append(self._mask_value_for_result(item))
                masked[placeholder] = masked_list
            else:
                masked[placeholder] = self._mask_value_for_result(value)
        return masked

    def mask_result_list(self, results: List[dict], column_mapping: Dict[str, str]) -> List[dict]:
        return [self.mask_result(r, column_mapping) for r in results]

    def unmask_text(self, text: str) -> str:
        result = text
        for col, placeholder in self._column_map.items():
            result = result.replace(placeholder, col)
        for prefix, rev_map in self._reverse_value_maps.items():
            for placeholder, real_val in rev_map.items():
                result = result.replace(placeholder, str(real_val))
        return result

    def get_column_mapping(self) -> Dict[str, str]:
        return dict(self._column_map)

    def get_reverse_mapping(self) -> Dict[str, str]:
        return dict(self._reverse_column_map)
