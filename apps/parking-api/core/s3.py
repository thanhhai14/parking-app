import boto3
from botocore.exceptions import ClientError
import logging
from typing import Optional
from core.config import settings

logger = logging.getLogger("parking-api")

class MinioClient:
    def __init__(self):
        protocol = "https" if settings.MINIO_SECURE else "http"
        self.endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}"
        
        # Internal client for uploads (uses internal docker endpoint, e.g. minio:9000)
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=boto3.session.Config(signature_version="s3v4"),
            verify=False
        )
        
        # Public client for generating presigned URLs (uses public endpoint, e.g. http://localhost:9000)
        self.public_client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_PUBLIC_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=boto3.session.Config(signature_version="s3v4"),
            verify=False
        )
        self.bucket_name = settings.MINIO_BUCKET

    def upload_fileobj(self, file_obj, object_key: str, content_type: str) -> bool:
        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key,
                ExtraArgs={"ContentType": content_type}
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file object to MinIO: {e}")
            return False

    def upload_bytes(self, file_data: bytes, object_key: str, content_type: str) -> bool:
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to upload bytes to MinIO: {e}")
            return False

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        try:
            url = self.public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

minio_client = MinioClient()
