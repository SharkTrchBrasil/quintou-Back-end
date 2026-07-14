import boto3
import uuid
import logging
from io import BytesIO
from typing import Optional
from fastapi import UploadFile
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(self):
        self.s3_client = None
        self.bucket = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

    def get_public_base_url(self) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com"

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = 'uploads',
        max_size_mb: int = 10,
        allowed_types: Optional[list] = None
    ) -> Optional[str]:
        """Upload a file to S3 and return the full public URL."""
        if not self.s3_client or not self.bucket:
            logger.error("S3 not configured, skipping upload")
            return None

        if allowed_types is None:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

        # Valida content_type
        if file.content_type not in allowed_types:
            logger.error(f"File type {file.content_type} not allowed")
            raise ValueError(f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_types)}")

        # Lê o conteúdo do arquivo
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)
        
        # Valida tamanho
        if file_size_mb > max_size_mb:
            logger.error(f"File too large: {file_size_mb:.2f}MB (max: {max_size_mb}MB)")
            raise ValueError(f"Arquivo muito grande: {file_size_mb:.2f}MB. Máximo: {max_size_mb}MB")

        # Valida nome do arquivo
        if not file.filename:
            raise ValueError("Nome do arquivo é obrigatório")

        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        
        # Sanitiza extensão
        ext = ext.lower()[:10]  # Previne extensões maliciosas
        
        file_key = f"{folder}/{uuid.uuid4()}.{ext}"

        try:
            self.s3_client.upload_fileobj(
                BytesIO(contents),
                self.bucket,
                file_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'CacheControl': 'public, max-age=31536000, immutable',
                }
            )
            logger.info(f"Upload successful: {file_key}")
            return f"{self.get_public_base_url()}/{file_key}"
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None

    async def delete_file(self, file_url: str) -> bool:
        """Delete a file from S3 by its public URL."""
        if not self.s3_client or not self.bucket:
            return False
        try:
            file_key = file_url.replace(f"{self.get_public_base_url()}/", "")
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_key)
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False
