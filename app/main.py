from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['linkedin_profiles']
collection = db['alumni_profiles']

# Pydantic model definitions
class Job(BaseModel):
    title: str
    company: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration: Optional[str]

class Institute(BaseModel):
    name: str
    degree: str
    start_year: Optional[str]
    end_year: Optional[str]

class AlumniProfile(BaseModel):
    name: str
    bio: str
    location: str
    contact_url: str
    contact: List[str]
    jobs: List[Job]
    institutes: List[Institute]

@app.get("/profiles/search")
async def search_profiles(
    name: Optional[str] = None,
    branch: Optional[str] = None,
    year: Optional[str] = None,
    company: Optional[str] = None
):
    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive search
    if branch:
        query["institutes.degree"] = {"$regex": branch, "$options": "i"}  # Branch search
    if year:
        query["institutes.start_year"] = year  # Start year search
    if company:
        query["jobs.company"] = {"$regex": company, "$options": "i"}  # Company search

    profiles = list(collection.find(query))
    if not profiles:
        raise HTTPException(status_code=404, detail="No profiles found matching the criteria.")
    for profile in profiles:
        profile["_id"] = str(profile["_id"])
    return profiles
# CRUD operations
@app.get("/profiles")
async def get_profiles():
    profiles = list(collection.find())
    for profile in profiles:
        profile["_id"] = str(profile["_id"])
    return profiles

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    profile = collection.find_one({"_id": ObjectId(profile_id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile["_id"] = str(profile["_id"])
    return profile

@app.post("/profiles")
async def create_profile(profile: AlumniProfile):
    result = collection.insert_one(profile.dict())
    return {"_id": str(result.inserted_id)}

@app.put("/profiles/{profile_id}")
async def update_profile(profile_id: str, profile: AlumniProfile):
    result = collection.update_one(
        {"_id": ObjectId(profile_id)}, {"$set": profile.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile updated successfully"}

@app.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    result = collection.delete_one({"_id": ObjectId(profile_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}

# Additional operations based on name, branch, year, and company

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
