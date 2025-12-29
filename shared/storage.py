"""
Shared MinIO/S3 storage utilities
"""
import os
from minio import Minio
from minio.error import S3Error
from typing import Optional
import io


class StorageClient:
    """MinIO storage client wrapper"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minio_password")
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False  # Set to True if using HTTPS
        )
        
        # Initialize buckets
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Create buckets if they don't exist"""
        buckets = ["audio", "videos", "models"]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
            except S3Error as e:
                print(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Upload file to MinIO"""
        try:
            self.client.fput_object(bucket, object_name, file_path)
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    def upload_bytes(self, bucket: str, object_name: str, data: bytes) -> bool:
        """Upload bytes to MinIO"""
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data)
            )
            return True
        except S3Error as e:
            print(f"Error uploading bytes: {e}")
            return False
    
    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Download file from MinIO"""
        try:
            self.client.fget_object(bucket, object_name, file_path)
            return True
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
    
    def get_object(self, bucket: str, object_name: str) -> Optional[bytes]:
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
    
    def delete_object(self, bucket: str, object_name: str) -> bool:
        """Delete object from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting object: {e}")
            return False
    
    def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> Optional[str]:
        """Get presigned URL for object"""
        try:
            url = self.client.presigned_get_object(bucket, object_name, expiry)
            return url
        except S3Error as e:
            print(f"Error getting presigned URL: {e}")
            return None


# Singleton instance
storage_client = StorageClient()

