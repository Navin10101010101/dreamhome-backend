import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
import logging
import os
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name='us-east-1'  # Ensure correct region
)

def secure_filename(filename: str):
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    return f"{uuid.uuid4()}.{ext}" if ext else f"{uuid.uuid4()}"

async def save_file_to_s3(file: UploadFile, bucket_name: str, file_path: str):
    try:
        s3_client.upload_fileobj(file.file, bucket_name, file_path)
        url = f"https://{bucket_name}.s3.amazonaws.com/{file_path}"
        logger.info(f"Successfully uploaded file to S3: {url}")
        return url
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        return None

async def save_file(file: UploadFile, file_path: str):
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, "wb") as buffer:
            chunk_size = 1024 * 1024  # 1MB chunks
            while content := await file.read(chunk_size):
                buffer.write(content)
        logger.info(f"Successfully saved file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save file {file.filename} to {file_path}: {str(e)}")
        return False

def normalize_images_field(images):
    default_images = {
        "exterior_view": [],
        "living_room": [],
        "bedrooms": [],
        "bathrooms": [],
        "kitchen": [],
        "floor_plan": [],
        "master_plan": [],
        "location_map": [],
        "others": []
    }
    if isinstance(images, list):
        return {**default_images, "others": images}
    elif isinstance(images, dict):
        return {**default_images, **images}
    else:
        return default_images