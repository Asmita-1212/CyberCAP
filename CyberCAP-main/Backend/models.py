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


from pydantic import BaseModel
from typing import List, Optional, Dict

class Complaint(BaseModel):
    incident_type: str
    incident_date: str
    incident_time: Optional[str] = None
    platform: str
    description: str                    # This will store translated text
    original_description: Optional[str] = None  # Add this field
    victim: Dict
    suspect: Dict
    attachments: List = []
    status: Optional[str] = None
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

class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str | None = None
    message: str