import uuid
import os
from fastapi import UploadFile

def secure_filename(filename: str):
    ext = filename.rsplit('.', 1)[-1]
    return f"{uuid.uuid4()}.{ext}"

async def save_file(file: UploadFile, file_path: str):
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

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
