import uuid
import os
from fastapi import UploadFile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def secure_filename(filename: str):
    ext = filename.rsplit('.', 1)[-1]
    return f"{uuid.uuid4()}.{ext}"

async def save_file(file: UploadFile, file_path: str):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        # Write file in chunks to handle large files
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