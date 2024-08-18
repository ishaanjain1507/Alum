from pydantic import BaseModel
from typing import List, Optional

class Job(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str
    duration: str

class Institute(BaseModel):
    name: str
    degree: str
    start_year: str
    end_year: str

class AlumniProfile(BaseModel):
    name: str
    bio: str
    location: str
    contact_url: str
    contact: List[str]
    jobs: List[Job]
    institutes: List[Institute]
