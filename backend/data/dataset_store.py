import uuid
from typing import Dict, List, Optional


class DatasetRecord:
    """In-memory record of an uploaded dataset. Stores only metadata, never raw data."""

    def __init__(self, dataset_id: str, filename: str, df, schema: List[Dict], rows: int, columns: int):
        self.dataset_id = dataset_id
        self.filename = filename
        self.df = df
        self.schema = schema
        self.rows = rows
        self.columns = columns


class DatasetStore:
    """Server-side temporary store for datasets. Datasets exist only in memory."""

    def __init__(self):
        self._datasets: Dict[str, DatasetRecord] = {}

    def save(self, filename: str, df, schema: List[Dict]) -> DatasetRecord:
        dataset_id = str(uuid.uuid4())[:12]
        rows = len(df)
        columns = len(df.columns)
        record = DatasetRecord(dataset_id, filename, df, schema, rows, columns)
        self._datasets[dataset_id] = record
        return record

    def get(self, dataset_id: str) -> Optional[DatasetRecord]:
        return self._datasets.get(dataset_id)

    def delete(self, dataset_id: str) -> bool:
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
            return True
        return False


dataset_store = DatasetStore()
