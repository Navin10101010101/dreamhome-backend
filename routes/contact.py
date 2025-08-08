from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from database import user_query_collection, property_collection
from bson import ObjectId
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["contact"])

class ContactRequest(BaseModel):
    name: str
    contact_no: str | None = None
    message: str
    property_id: str

    @validator('name', 'message')
    def not_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Name and message cannot be empty')
        return v

    @validator('contact_no', pre=True, always=True)
    def contact_no_optional(cls, v):
        if v is not None and not v.strip().isdigit():
            raise ValueError('Contact number must contain only digits')
        return v

@router.post("/contact-owner")
async def contact_owner(request: ContactRequest):
    try:
        # Validate property_id
        property_doc = property_collection.find_one({"_id": ObjectId(request.property_id)})
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")

        # Store query in User Query collection
        query_data = {
            "name": request.name.strip(),
            "contact_no": request.contact_no.strip() if request.contact_no else "",
            "message": request.message.strip(),
            "property_id": request.property_id,
            "createdAt": datetime.now(),
        }
        result = user_query_collection.insert_one(query_data)
        logger.info(f"Query submitted successfully for property {request.property_id}, query_id: {str(result.inserted_id)}")
        return {"message": "Query submitted successfully", "query_id": str(result.inserted_id)}
    except HTTPException as http_err:
        raise http_err
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error processing contact request: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")