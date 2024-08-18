from fastapi import APIRouter, HTTPException
from .crud import add_alumni, get_alumni, get_all_alumni
from .models import Alumni

router = APIRouter()

@router.post("/alumni/")
def create_alumni(alumni: Alumni):
    add_alumni(alumni)
    return {"message": "Alumni added successfully"}

@router.get("/alumni/{name}")
def read_alumni(name: str):
    alumni = get_alumni(name)
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")
    return alumni

@router.get("/alumni/")
def read_all_alumni():
    return get_all_alumni()
