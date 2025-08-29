from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class Complaint(BaseModel):
    user_id: str
    complaint_text: str
    attachment: str | None = None
