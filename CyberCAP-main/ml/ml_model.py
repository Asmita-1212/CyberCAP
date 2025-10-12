# Backend/models.py
from pydantic import BaseModel
from typing import List, Optional

class PersonDetails(BaseModel):
    full_name: str
    gender: str
    dob: str
    address: str
    state: str
    district: str
    email: str
    mobile: str

class SuspectDetails(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    social_handle: Optional[str] = None
    bank_account: Optional[str] = None

class Complaint(BaseModel):
    incident_type: str
    incident_date: str
    incident_time: Optional[str] = None
    platform: str
    description: str
    attachments: Optional[List[str]] = []
    victim: PersonDetails
    suspect: Optional[SuspectDetails] = None
