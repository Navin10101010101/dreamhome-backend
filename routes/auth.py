from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import user_collection
from auth import hash_password, verify_password, create_access_token
from bson import ObjectId

router = APIRouter(prefix="/api", tags=["auth"])

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user: UserRegister):
    if user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = hash_password(user.password)
    user_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    })
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: UserLogin):
    db_user = user_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(db_user["_id"]), "email": db_user["email"]})
    return {"access_token": token, "token_type": "bearer"}
