from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.property import router as property_router
from routes.contact import router as contact_router

app = FastAPI(title="DreamHome API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://dreamhome-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the uploads directory to serve images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(property_router, prefix="/api")
app.include_router(contact_router, prefix="/api")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "DreamHome API is running"}