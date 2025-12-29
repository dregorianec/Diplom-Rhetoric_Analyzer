"""
Shared MinIO/S3 storage utilities
"""
import os
from minio import Minio
from minio.error import S3Error
from typing import Optional
import io


class StorageClient:
    """MinIO storage client wrapper with lazy initialization"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minio_password")
        self._client = None
        self._initialized = False
    
    @property
    def client(self) -> Minio:
        """Lazy initialization of MinIO client"""
        if self._client is None:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=False  # Set to True if using HTTPS
            )
        return self._client
    
    def _ensure_buckets(self):
        """Create buckets if they don't exist"""
        if self._initialized:
            return
            
        buckets = ["audio", "videos", "models"]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
            except S3Error as e:
                print(f"Error creating bucket {bucket}: {e}")
        self._initialized = True
    
    def upload_file(self, file_path: str, object_name: str, bucket: str = "audio") -> bool:
        """
        Upload file to MinIO
        
        Args:
            file_path: Local path to file
            object_name: Name/path in bucket (e.g. "politician/video_id.mp3")
            bucket: Bucket name (default: "audio")
        """
        try:
            self._ensure_buckets()
            self.client.fput_object(bucket, object_name, file_path)
            return True
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise
    
    def upload_bytes(self, data: bytes, object_name: str, bucket: str = "audio") -> bool:
        """Upload bytes to MinIO"""
        try:
            self._ensure_buckets()
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data)
            )
            return True
        except Exception as e:
            print(f"Error uploading bytes: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str, bucket: str = "audio") -> bool:
        """Download file from MinIO"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            return True
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
    
    def get_object(self, object_name: str, bucket: str = "audio") -> Optional[bytes]:
        """Get object as bytes"""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"Error getting object: {e}")
            return None
    
    def delete_object(self, object_name: str, bucket: str = "audio") -> bool:
        """Delete object from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting object: {e}")
            return False
    
    def get_presigned_url(self, object_name: str, bucket: str = "audio", expiry: int = 3600) -> Optional[str]:
        """Get presigned URL for object"""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expiry))
            return url
        except S3Error as e:
            print(f"Error getting presigned URL: {e}")
            return None
    
    def list_objects(self, prefix: str = "", bucket: str = "audio") -> list:
        """List objects in bucket with optional prefix"""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []


# Singleton instance
storage_client = StorageClient()
