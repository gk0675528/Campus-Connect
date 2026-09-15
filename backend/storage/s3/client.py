"""S3 Client for File Storage"""

from core.config.settings import settings
import boto3
from core.config.logging import logger


class S3Client:
    """AWS S3 Storage Client"""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
    
    async def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to S3"""
        
        try:
            self.client.upload_file(
                file_path,
                settings.AWS_S3_BUCKET_NAME,
                key
            )
            
            url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"File uploaded to S3: {url}")
            return url
            
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        
        try:
            self.client.delete_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=key
            )
            
            logger.info(f"File deleted from S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"S3 delete error: {str(e)}")
            return False
    
    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file"""
        
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key},
                ExpiresIn=expiration
            )
            return url
            
        except Exception as e:
            logger.error(f"Presigned URL generation error: {str(e)}")
            raise
