from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Union
from database import property_collection, user_collection
from auth import decode_access_token
from utils.file_utils import secure_filename, save_file, normalize_images_field
from datetime import datetime
from bson import ObjectId
import json
import os

router = APIRouter(prefix="/api", tags=["properties"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

class PropertyResponse(BaseModel):
    id: str
    title: str
    propertyType: str
    price: str
    location: Union[Dict, str]
    bhk: Optional[str] = None
    description: Optional[str] = None
    images: Dict[str, List[str]]
    createdAt: str
    negotiable: Optional[str] = None
    availabilityStatus: Optional[str] = None
    propertyStatus: Optional[str] = None
    amenities: Optional[Dict] = None
    listedBy: Optional[str] = None
    propertyFeatures: Optional[Dict] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

@router.post("/properties")
async def create_property(
    formData: str = Form(...),
    exterior_view: List[UploadFile] = File(default=[]),
    living_room: List[UploadFile] = File(default=[]),
    bedrooms: List[UploadFile] = File(default=[]),
    bathrooms: List[UploadFile] = File(default=[]),
    kitchen: List[UploadFile] = File(default=[]),
    floor_plan: List[UploadFile] = File(default=[]),
    master_plan: List[UploadFile] = File(default=[]),
    location_map: List[UploadFile] = File(default=[]),
    others: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[]),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("sub")
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        data = json.loads(formData)
        os.makedirs("uploads/images", exist_ok=True)
        os.makedirs("uploads/videos", exist_ok=True)

        image_urls = {
            "exterior_view": [], "living_room": [], "bedrooms": [], "bathrooms": [],
            "kitchen": [], "floor_plan": [], "master_plan": [], "location_map": [], "others": []
        }
        file_paths = []
        for category, files in [
            ("exterior_view", exterior_view), ("living_room", living_room), ("bedrooms", bedrooms),
            ("bathrooms", bathrooms), ("kitchen", kitchen), ("floor_plan", floor_plan),
            ("master_plan", master_plan), ("location_map", location_map), ("others", others)
        ]:
            for img in files:
                if img.size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
                safe_name = secure_filename(img.filename)
                file_path = f"uploads/images/{safe_name}"
                await save_file(img, file_path)
                image_urls[category].append(file_path)
                file_paths.append(file_path)

        video_urls = []
        for video in videos:
            if video.size > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Video too large (max 50MB)")
            safe_name = secure_filename(video.filename)
            file_path = f"uploads/videos/{safe_name}"
            await save_file(video, file_path)
            video_urls.append(file_path)
            file_paths.append(file_path)

        personal = data.get("personalDetails", {})
        property_info = data.get("propertyDetails", {})
        features = data.get("propertyFeatures", {})
        location = data.get("locationDetails", {})

        residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
        land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
        property_data = {
            "title": property_info.get("title"),
            "propertyType": property_info.get("propertyType"),
            "price": property_info.get("price"),
            "negotiable": property_info.get("negotiable"),
            "location": {
                "state": location.get("state"),
                "city": location.get("city"),
                "locality": location.get("locality"),
                "address": location.get("address"),
                "pinCode": location.get("pinCode"),
                "landmarks": location.get("landmarks")
            },
            "images": image_urls,
            "videos": video_urls,
            "createdAt": datetime.now(),
            "listedBy": user_id,
            "personalDetails": personal,
        }

        if property_info.get("propertyType") in residential_types:
            property_data.update({
                "availabilityStatus": property_info.get("availabilityStatus"),
                "propertyStatus": property_info.get("propertyStatus"),
                "bhk": features.get("bhk"),
                "amenities": {
                    "parking": features.get("parking", "No"),
                    "lift": features.get("lift", "No"),
                    "security": features.get("security", "No"),
                    "powerBackup": features.get("powerBackup", "No"),
                    "waterSupply": features.get("waterSupply", "No"),
                    "boundaryWall": features.get("boundaryWall", "No"),
                    "gatedCommunity": features.get("gatedCommunity", "No"),
                    "bathrooms": features.get("bathrooms", "1"),
                    "totalFloors": features.get("totalFloors", "N/A"),
                    "floorNo": features.get("floorNo", "N/A"),
                    "furnishing": features.get("furnishing", "N/A"),
                    "builtupArea": features.get("builtupArea", "N/A"),
                    "carpetArea": features.get("carpetArea", "N/A")
                },
                "propertyFeatures": features,
            })
        elif property_info.get("propertyType") in land_types:
            property_data.update({
                "amenities": {
                    "parking": features.get("parking", "No"),
                    "security": features.get("security", "No"),
                    "powerBackup": features.get("powerBackup", "No"),
                    "waterSupply": features.get("waterSupply", "No"),
                    "boundaryWall": features.get("boundaryWall", "No"),
                    "gatedCommunity": features.get("gatedCommunity", "No"),
                },
                "propertyFeatures": {
                    "areaUnit": features.get("areaUnit", "N/A"),
                    "areaValue": features.get("areaValue", "N/A"),
                    "anyConstructionDone": features.get("anyConstructionDone", "No"),
                    "plotFacing": features.get("plotFacing", "N/A"),
                    "transactionType": features.get("transactionType", "N/A"),
                    "roadAccessType": features.get("roadAccessType", "N/A"),
                }
            })
        else:  # Office
            property_data.update({
                "amenities": {
                    "parking": features.get("parking", "No"),
                    "security": features.get("security", "No"),
                    "powerBackup": features.get("powerBackup", "No"),
                    "waterSupply": features.get("waterSupply", "No"),
                    "boundaryWall": features.get("boundaryWall", "No"),
                    "gatedCommunity": features.get("gatedCommunity", "No"),
                    "lift": features.get("lift", "No"),
                    "internet": features.get("internet", "No"),
                    "publicTransport": features.get("publicTransport", "No"),
                    "pantry": features.get("pantry", "Not Available"),
                    "washroom": features.get("washroom", "Not Available"),
                },
                "propertyFeatures": {
                    "carpetArea": features.get("carpetArea", "N/A"),
                    "floorNo": features.get("floorNo", "N/A"),
                    "furnishing": features.get("furnishing", "N/A"),
                    "cabins": features.get("cabins", "N/A"),
                    "workstations": features.get("workstations", "N/A"),
                    "roadAccessType": features.get("roadAccessType", "N/A"),
                }
            })

        result = property_collection.insert_one(property_data)
        return {"status": "success", "property_id": str(result.inserted_id)}
    except Exception as e:
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/properties", response_model=List[PropertyResponse])
async def get_user_properties(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    properties = list(property_collection.find({"listedBy": user_id}))
    residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
    land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
    
    for prop in properties:
        prop["id"] = str(prop["_id"])
        prop["createdAt"] = prop["createdAt"].isoformat()
        prop["images"] = normalize_images_field(prop.get("images", []))
        prop["negotiable"] = prop.get("negotiable", "No")
        
        if prop.get("propertyType") in residential_types:
            prop["availabilityStatus"] = prop.get("availabilityStatus", "Ready to Move")
            prop["propertyStatus"] = prop.get("propertyStatus", "New Project")
            prop["bhk"] = prop.get("bhk", "N/A")
            features = prop.get("propertyFeatures", {})
            prop["amenities"] = {
                **{
                    "parking": "No", "lift": "No", "security": "No", "powerBackup": "No",
                    "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No", "bathrooms": "1"
                },
                **prop.get("amenities", {}),
                **{
                    "totalFloors": features.get("totalFloors", "N/A"),
                    "floorNo": features.get("floorNo", "N/A"),
                    "furnishing": features.get("furnishing", "N/A"),
                    "builtupArea": features.get("builtupArea", "N/A"),
                    "carpetArea": features.get("carpetArea", "N/A")
                }
            }
        elif prop.get("propertyType") in land_types:
            prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
            prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
            prop["bhk"] = prop.get("bhk", "N/A")
            features = prop.get("propertyFeatures", {})
            prop["amenities"] = {
                **{
                    "parking": "No", "security": "No", "powerBackup": "No",
                    "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No"
                },
                **prop.get("amenities", {}),
            }
            prop["propertyFeatures"] = {
                **{
                    "areaUnit": "N/A",
                    "areaValue": "N/A",
                    "anyConstructionDone": "No",
                    "plotFacing": "N/A",
                    "transactionType": "N/A",
                    "roadAccessType": "N/A"
                },
                **features
            }
        else:  # Office
            prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
            prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
            prop["bhk"] = prop.get("bhk", "N/A")
            features = prop.get("propertyFeatures", {})
            prop["amenities"] = {
                **{
                    "parking": "No", "security": "No", "powerBackup": "No",
                    "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No",
                    "lift": "No", "internet": "No", "publicTransport": "No",
                    "pantry": "Not Available", "washroom": "Not Available"
                },
                **prop.get("amenities", {}),
            }
            prop["propertyFeatures"] = {
                **{
                    "carpetArea": "N/A", "floorNo": "N/A", "furnishing": "N/A",
                    "cabins": "N/A", "workstations": "N/A", "roadAccessType": "N/A"
                },
                **features
            }
        
        prop["listedBy"] = prop.get("listedBy", "Unknown")
    return properties

@router.get("/properties", response_model=List[PropertyResponse])
async def get_properties():
    try:
        properties = []
        residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
        land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
        for prop in property_collection.find():
            prop["id"] = str(prop["_id"])
            prop["createdAt"] = prop["createdAt"].isoformat()
            if isinstance(prop.get("location"), str):
                prop["location"] = {"city": prop["location"], "state": ""}
            prop["description"] = prop.get("description", "")
            prop["images"] = normalize_images_field(prop.get("images", []))
            prop["negotiable"] = prop.get("negotiable", "No")
            
            if prop.get("propertyType") in residential_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "Ready to Move")
                prop["propertyStatus"] = prop.get("propertyStatus", "New Project")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "lift": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No", "bathrooms": "1"
                    },
                    **prop.get("amenities", {}),
                    **{
                        "totalFloors": features.get("totalFloors", "N/A"),
                        "floorNo": features.get("floorNo", "N/A"),
                        "furnishing": features.get("furnishing", "N/A"),
                        "builtupArea": features.get("builtupArea", "N/A"),
                        "carpetArea": features.get("carpetArea", "N/A")
                    }
                }
            elif prop.get("propertyType") in land_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "areaUnit": "N/A",
                        "areaValue": "N/A",
                        "anyConstructionDone": "No",
                        "plotFacing": "N/A",
                        "transactionType": "N/A",
                        "roadAccessType": "N/A"
                    },
                    **features
                }
            else:  # Office
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No",
                        "lift": "No", "internet": "No", "publicTransport": "No",
                        "pantry": "Not Available", "washroom": "Not Available"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "carpetArea": "N/A", "floorNo": "N/A", "furnishing": "N/A",
                        "cabins": "N/A", "workstations": "N/A", "roadAccessType": "N/A"
                    },
                    **features
                }
                
            prop["listedBy"] = prop.get("listedBy", "Unknown")
            properties.append(prop)
        return properties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/properties/filtered", response_model=List[PropertyResponse])
async def get_filtered_properties(
    location: Optional[str] = None,
    priceMin: Optional[str] = None,
    priceMax: Optional[str] = None,
    bhk: Optional[str] = None,
    propertyType: Optional[str] = None,
    availabilityStatus: Optional[str] = None,
    propertyStatus: Optional[str] = None,
    parking: Optional[str] = None,
    lift: Optional[str] = None,
    security: Optional[str] = None,
    anyConstructionDone: Optional[str] = None,
    plotFacing: Optional[str] = None,
    transactionType: Optional[str] = None,
    internet: Optional[str] = None,
    publicTransport: Optional[str] = None,
    search: Optional[str] = None
):
    try:
        query = {}
        if location:
            query["location.city"] = {"$regex": location, "$options": "i"}
        if priceMin or priceMax:
            query["price"] = {}
            try:
                if priceMin:
                    query["price"]["$gte"] = float(priceMin)
                if priceMax:
                    query["price"]["$lte"] = float(priceMax)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid price format")
        if bhk:
            query["bhk"] = bhk
        if propertyType:
            query["propertyType"] = {"$regex": propertyType, "$options": "i"}
        if availabilityStatus:
            query["availabilityStatus"] = availabilityStatus
        if propertyStatus:
            query["propertyStatus"] = propertyStatus
        if parking:
            query["amenities.parking"] = parking
        if lift:
            query["amenities.lift"] = lift
        if security:
            query["amenities.security"] = security
        if anyConstructionDone:
            query["propertyFeatures.anyConstructionDone"] = anyConstructionDone
        if plotFacing:
            query["propertyFeatures.plotFacing"] = {"$in": [plotFacing, "N/A"]}
        if transactionType:
            query["propertyFeatures.transactionType"] = transactionType
        if internet:
            query["amenities.internet"] = internet
        if publicTransport:
            query["amenities.publicTransport"] = publicTransport
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"location.city": {"$regex": search, "$options": "i"}}
            ]

        properties = []
        residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
        land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
        for prop in property_collection.find(query):
            prop["id"] = str(prop["_id"])
            prop["createdAt"] = prop["createdAt"].isoformat()
            if isinstance(prop.get("location"), str):
                prop["location"] = {"city": prop["location"], "state": ""}
            prop["description"] = prop.get("description", "")
            prop["images"] = normalize_images_field(prop.get("images", []))
            prop["negotiable"] = prop.get("negotiable", "No")
            
            if prop.get("propertyType") in residential_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "Ready to Move")
                prop["propertyStatus"] = prop.get("propertyStatus", "New Project")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "lift": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No", "bathrooms": "1"
                    },
                    **prop.get("amenities", {}),
                    **{
                        "totalFloors": features.get("totalFloors", "N/A"),
                        "floorNo": features.get("floorNo", "N/A"),
                        "furnishing": features.get("furnishing", "N/A"),
                        "builtupArea": features.get("builtupArea", "N/A"),
                        "carpetArea": features.get("carpetArea", "N/A")
                    }
                }
            elif prop.get("propertyType") in land_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["propertyFeatures"] = {
                    **{
                        "areaUnit": "N/A",
                        "areaValue": "N/A",
                        "anyConstructionDone": "No",
                        "plotFacing": "N/A",
                        "transactionType": "N/A",
                        "roadAccessType": "N/A"
                    },
                    **features
                }
            else:  # Office
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No",
                        "lift": "No", "internet": "No", "publicTransport": "No",
                        "pantry": "Not Available", "washroom": "Not Available"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "carpetArea": "N/A", "floorNo": "N/A", "furnishing": "N/A",
                        "cabins": "N/A", "workstations": "N/A", "roadAccessType": "N/A"
                    },
                    **features
                }
                
            prop["listedBy"] = prop.get("listedBy", "Unknown")
            properties.append(prop)
        return properties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/properties/offices", response_model=List[PropertyResponse])
async def get_office_properties():
    try:
        properties = []
        residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
        land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
        for prop in property_collection.find({"propertyType": "Office"}).sort("createdAt", -1).limit(4):
            prop["id"] = str(prop["_id"])
            prop["createdAt"] = prop["createdAt"].isoformat()
            if isinstance(prop.get("location"), str):
                prop["location"] = {"city": prop["location"], "state": ""}
            prop["description"] = prop.get("description", "")
            prop["images"] = normalize_images_field(prop.get("images", []))
            prop["negotiable"] = prop.get("negotiable", "No")
            
            if prop.get("propertyType") in residential_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "Ready to Move")
                prop["propertyStatus"] = prop.get("propertyStatus", "New Project")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "lift": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No", "bathrooms": "1"
                    },
                    **prop.get("amenities", {}),
                    **{
                        "totalFloors": features.get("totalFloors", "N/A"),
                        "floorNo": features.get("floorNo", "N/A"),
                        "furnishing": features.get("furnishing", "N/A"),
                        "builtupArea": features.get("builtupArea", "N/A"),
                        "carpetArea": features.get("carpetArea", "N/A")
                    }
                }
            elif prop.get("propertyType") in land_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "areaUnit": "N/A",
                        "areaValue": "N/A",
                        "anyConstructionDone": "No",
                        "plotFacing": "N/A",
                        "transactionType": "N/A",
                        "roadAccessType": "N/A"
                    },
                    **features
                }
            else:  # Office
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No",
                        "lift": "No", "internet": "No", "publicTransport": "No",
                        "pantry": "Not Available", "washroom": "Not Available"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "carpetArea": "N/A", "floorNo": "N/A", "furnishing": "N/A",
                        "cabins": "N/A", "workstations": "N/A", "roadAccessType": "N/A"
                    },
                    **features
                }
                
            prop["listedBy"] = prop.get("listedBy", "Unknown")
            properties.append(prop)
        return properties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/properties/land", response_model=List[PropertyResponse])
async def get_land_properties():
    try:
        properties = []
        residential_types = ["Flat", "Apartment", "Villa", "House", "Farm House"]
        land_types = ["Residential Land", "Commercial Land", "Agriculture Land"]
        for prop in property_collection.find({"propertyType": {"$in": land_types}}).sort("createdAt", -1).limit(4):
            prop["id"] = str(prop["_id"])
            prop["createdAt"] = prop["createdAt"].isoformat()
            if isinstance(prop.get("location"), str):
                prop["location"] = {"city": prop["location"], "state": ""}
            prop["description"] = prop.get("description", "")
            prop["images"] = normalize_images_field(prop.get("images", []))
            prop["negotiable"] = prop.get("negotiable", "No")
            
            if prop.get("propertyType") in residential_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "Ready to Move")
                prop["propertyStatus"] = prop.get("propertyStatus", "New Project")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "lift": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No", "bathrooms": "1"
                    },
                    **prop.get("amenities", {}),
                    **{
                        "totalFloors": features.get("totalFloors", "N/A"),
                        "floorNo": features.get("floorNo", "N/A"),
                        "furnishing": features.get("furnishing", "N/A"),
                        "builtupArea": features.get("builtupArea", "N/A"),
                        "carpetArea": features.get("carpetArea", "N/A")
                    }
                }
            elif prop.get("propertyType") in land_types:
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "areaUnit": "N/A",
                        "areaValue": "N/A",
                        "anyConstructionDone": "No",
                        "plotFacing": "N/A",
                        "transactionType": "N/A",
                        "roadAccessType": "N/A"
                    },
                    **features
                }
            else:  # Office
                prop["availabilityStatus"] = prop.get("availabilityStatus", "N/A")
                prop["propertyStatus"] = prop.get("propertyStatus", "N/A")
                prop["bhk"] = prop.get("bhk", "N/A")
                features = prop.get("propertyFeatures", {})
                prop["amenities"] = {
                    **{
                        "parking": "No", "security": "No", "powerBackup": "No",
                        "waterSupply": "No", "boundaryWall": "No", "gatedCommunity": "No",
                        "lift": "No", "internet": "No", "publicTransport": "No",
                        "pantry": "Not Available", "washroom": "Not Available"
                    },
                    **prop.get("amenities", {}),
                }
                prop["propertyFeatures"] = {
                    **{
                        "carpetArea": "N/A", "floorNo": "N/A", "furnishing": "N/A",
                        "cabins": "N/A", "workstations": "N/A", "roadAccessType": "N/A"
                    },
                    **features
                }
                
            prop["listedBy"] = prop.get("listedBy", "Unknown")
            properties.append(prop)
        return properties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))