from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserSummary(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    department: str
    division: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    mobile: str
    full_name: str
    role: str
    department: str
    division: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserCreate(BaseModel):
    username: str
    email: str
    mobile: str
    password: str
    full_name: str
    role: str
    department: Optional[str] = "Revenue & Forest Department"
    division: Optional[str] = "Pune Division"
    is_active: Optional[bool] = True
