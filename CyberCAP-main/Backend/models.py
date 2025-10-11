from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str


from pydantic import BaseModel, EmailStr, Field
from typing import Optional,List

class Suspect(BaseModel):
    phone: Optional[str] = Field(None, pattern=r'^\d{10}$')
    email: Optional[EmailStr] = None
    social_handle: Optional[str]
    bank_account: Optional[str]

class Victim(BaseModel):
    full_name: str
    gender: str
    dob: str
    address: str
    state: str
    district: str
    email: EmailStr
    mobile: str = Field(..., pattern=r'^\d{10}$')


class Complaint(BaseModel):
    incident_type: str
    incident_date: str
    incident_time: Optional[str] = None
    platform: str
    description: str
    attachments: Optional[List[str]] = []
    victim: Victim         # <-- Nested Victim object
    suspect: Optional[Suspect] = None
    status: Optional[str] = "Pending"
    priority: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[str] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminMFA(BaseModel):
    username: str
    otp: str

class Volunteers(BaseModel):
    name: str
    email: str
    mobile: str
    role: str
    state: str
    expertise: str = None
    message: str