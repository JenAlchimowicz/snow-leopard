import boto3
import polars as pl
from typing import List
from io import BytesIO
from data.loaders.storage.StorageClient import StorageClient


class S3StorageClient(StorageClient):
    def __init__(self, bucket_name: str, base_path: str = "data"):
        self.bucket_name = bucket_name
        self.base_path = base_path.rstrip('/')
        self.s3_client = boto3.client('s3')
    
    def _full_path(self, path: str) -> str:
        """Construct full S3 key with base_path prefix"""
        return f"{self.base_path}/{path}"
    
    def upload_polars_df(self, df: pl.DataFrame, dest_path: str) -> None:
        buffer = BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self._full_path(dest_path),
            Body=buffer.getvalue()
        )
    
    def load_file_to_polars_df(self, source_path: str) -> pl.DataFrame:
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=self._full_path(source_path)
        )
        return pl.read_parquet(BytesIO(response['Body'].read()))
    
    def load_files_to_polars_df(self, source_paths: List[str]) -> pl.DataFrame:
        good_file = f"{self.base_path}/2025-12-03"
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=good_file
        )
        schema = pl.read_parquet_schema(BytesIO(response['Body'].read()))
        
        file_buffers = []
        for source_path in source_paths:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self._full_path(source_path)
            )
            file_buffers.append(BytesIO(response['Body'].read()))
        
        return (
            pl.scan_parquet(
                file_buffers,
                schema=schema,
                missing_columns="insert",
            )
            .collect()
        )
    
    def list_files(self, prefix: str = "") -> List[str]:
        full_prefix = self._full_path(prefix) if prefix else self.base_path + "/"
        
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=full_prefix
        )
        
        if 'Contents' not in response:
            return []
        
        # Return only the keys (file paths) with base_path stripped
        base_len = len(self.base_path) + 1  # +1 for the slash
        return [obj['Key'][base_len:] for obj in response['Contents']]
    
    def delete_file(self, path: str) -> None:
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=self._full_path(path)
            )
        except self.s3_client.exceptions.NoSuchKey:
            print(f"delete_file: File not found: {path}")
        except Exception as e:
            print(f"delete_file: Failed to delete {path}: {e}")
    
    def exists(self, path: str) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=self._full_path(path)
            )
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False
