from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MaskingConfig:
    column_mapping: Dict[str, str] = field(default_factory=dict)
    reverse_column_mapping: Dict[str, str] = field(default_factory=dict)
    value_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)
    reverse_value_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)
