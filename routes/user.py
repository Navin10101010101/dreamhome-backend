from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from database import user_collection
from auth import decode_access_token, verify_password, hash_password
from bson import ObjectId

router = APIRouter(prefix="/api", tags=["user"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

class UserResponse(BaseModel):
    name: str
    email: str

class UpdateUserRequest(BaseModel):
    name: str
    email: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/user", response_model=UserResponse)
async def get_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    user = user_collection.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user["name"], "email": user["email"]}

@router.put("/user/update")
async def update_user(request: UpdateUserRequest, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if request.email != user["email"] and user_collection.find_one({"email": request.email}):
        raise HTTPException(status_code=400, detail="Email already in use")
    update_data = {"name": request.name, "email": request.email}
    user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    return {"message": "Profile updated successfully"}

@router.put("/user/change-password")
async def change_password(request: ChangePasswordRequest, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(request.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    hashed_new_password = hash_password(request.new_password)
    user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_new_password}})
    return {"message": "Password changed successfully"}