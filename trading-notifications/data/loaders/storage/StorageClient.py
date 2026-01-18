import abc
from typing import List
import polars as pl

class StorageClient(abc.ABC):

    @abc.abstractmethod
    def upload_polars_df(self, df: pl.DataFrame, dest_path: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def load_file_to_polars_df(self, source_path: str) -> pl.DataFrame:
        raise NotImplementedError
    
    @abc.abstractmethod
    def load_files_to_polars_df(self, source_paths: List[str]) -> pl.DataFrame:
        raise NotImplementedError

    @abc.abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_file(self, path: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError
