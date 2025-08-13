from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UserCreate(BaseModel):
    name: str 
    email: EmailStr 
    aptech_branch: str 
    skills: List[str] 
    photo: Optional[str] 
    student_card_picture: Optional[str]

class UserInDB(UserCreate):
    id: Optional[str] = None
    dob: Optional[str] = None  # For extracted DOB from card 