from data.loaders.storage.StorageClient import StorageClient
from config import Config
import polars as pl
from typing import List
import os

class LocalStorageClient(StorageClient):
    def __init__(self):
        self.base_path = Config.LOCAL_DATA_PATH

    def upload_polars_df(self, df: pl.DataFrame, dest_path: str) -> None:
        full_path = f"{self.base_path}/{dest_path}"
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        df.write_parquet(full_path)

    def load_file_to_polars_df(self, source_path: str) -> pl.DataFrame:
        return pl.read_parquet(f"{self.base_path}/{source_path}")

    def load_files_to_polars_df(self, source_paths: List[str]) -> pl.DataFrame:
        good_file = f"{self.base_path}/2025-12-03"
        schema = pl.read_parquet_schema(good_file)
        return (
            pl.scan_parquet(
                [f"{self.base_path}/{source_path}" for source_path in source_paths],
                schema=schema,
                missing_columns="insert",
            )
            .collect()
        )

    def list_files(self, prefix: str = "") -> List[str]:
        return os.listdir(f"{self.base_path}/{prefix}")

    def delete_file(self, path: str) -> None:
        full_path = f"{self.base_path}/{path}"
        try:
            os.remove(full_path)
        except FileNotFoundError:
            print(f"delete_file: File not found: {full_path}")
        except Exception as e:
            print(f"delete_file: Failed to delete {full_path}: {e}")

    def exists(self, path: str) -> bool:
        return os.path.exists(f"{self.base_path}/{path}")
