import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.config import settings
import uuid

class UploadService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME

    def generate_presigned_url(self, file_name: str, file_type: str) -> dict:
        """Gera uma URL pre-assinada para o front-end fazer upload direto para o S3."""
        if not self.bucket:
            # Fallback para desenvolvimento sem AWS configurada
            return {"url": "http://localhost:8000/mocked-upload-url", "key": file_name}
            
        ext = file_name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{ext}"
        
        try:
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=unique_filename,
                Fields={"Content-Type": file_type},
                Conditions=[
                    {"Content-Type": file_type},
                    ["content-length-range", 0, 10485760] # max 10MB
                ],
                ExpiresIn=3600 # 1 hora
            )
            return {
                "upload_data": presigned_post,
                "file_url": f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
            }
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))
