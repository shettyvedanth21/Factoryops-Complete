"""S3 client for dataset access."""

from typing import List, Optional

import aioboto3
import structlog

from src.config.settings import get_settings

logger = structlog.get_logger()


class S3Client:
    """Async S3 client for downloading datasets."""
    
    def __init__(self):
        self._settings = get_settings()
        self._logger = logger.bind(service="S3Client")
        self._bucket = self._settings.s3_bucket_name
        self._session = aioboto3.Session()
    
    async def download_file(self, key: str) -> bytes:
        """
        Download file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            File contents as bytes
        """
        async with self._session.client(
            "s3",
            region_name=self._settings.s3_region,
            aws_access_key_id=self._settings.s3_access_key_id or None,
            aws_secret_access_key=self._settings.s3_secret_access_key or None,
        ) as client:
            self._logger.debug("downloading_file", bucket=self._bucket, key=key)
            
            response = await client.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                data = await stream.read()
            
            self._logger.debug("file_downloaded", bucket=self._bucket, key=key, size=len(data))
            return data
    
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> List[dict]:
        """
        List objects in S3 bucket.
        
        Args:
            prefix: Key prefix filter
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object metadata
        """
        async with self._session.client(
            "s3",
            region_name=self._settings.s3_region,
        ) as client:
            response = await client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            
            objects = response.get("Contents", [])
            return [
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
                for obj in objects
            ]
    
    async def upload_file(self, key: str, data: bytes) -> None:
        """
        Upload file to S3.
        
        Args:
            key: S3 object key
            data: File contents as bytes
        """
        async with self._session.client(
            "s3",
            region_name=self._settings.s3_region,
        ) as client:
            self._logger.debug("uploading_file", bucket=self._bucket, key=key)
            
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
            )
            
            self._logger.debug("file_uploaded", bucket=self._bucket, key=key)
