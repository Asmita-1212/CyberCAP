from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

from pydantic import BaseModel
from typing import List, Optional

class Suspect(BaseModel):
    phone: Optional[str]
    email: Optional[str]
    social_handle: Optional[str]
    bank_account: Optional[str]

class Victim(BaseModel):
    full_name: str
    gender: str
    dob: str
    address: str
    state: str
    district: str
    email: str
    mobile: str

class Complaint(BaseModel):
    incident_type: str
    incident_date: str
    incident_time: Optional[str]
    platform: str
    description: str
    suspect: Optional[Suspect]
    victim: Victim
    attachments: Optional[List[str]] = []
    priority: Optional[str] = None
    category: Optional[str] = None


from pydantic import BaseModel

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminMFA(BaseModel):
    username: str
    otp: str

