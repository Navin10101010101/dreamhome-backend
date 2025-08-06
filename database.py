from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["dreamhome"]
user_collection = db["users"]
property_collection = db["properties"]
user_activities_collection = db["user_activities"]
user_query_collection = db["User Query"]