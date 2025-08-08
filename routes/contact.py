from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import user_query_collection, property_collection
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api", tags=["contact"])

class ContactRequest(BaseModel):
    name: str
    contact_no: str | None = None
    message: str
    property_id: str

@router.post("/contact-owner")
async def contact_owner(request: ContactRequest):
    try:
        # Validate property_id
        if not property_collection.find_one({"_id": ObjectId(request.property_id)}):
            raise HTTPException(status_code=404, detail="Property not found")

        # Store query in User Query collection
        query_data = {
            "name": request.name,
            "contact_no": request.contact_no or "",
            "message": request.message,
            "property_id": request.property_id,
            "createdAt": datetime.now(),
        }
        result = user_query_collection.insert_one(query_data)
        return {"message": "Query submitted successfully", "query_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))