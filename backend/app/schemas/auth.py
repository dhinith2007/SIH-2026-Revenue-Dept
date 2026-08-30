from typing import List, Optional
from pydantic import BaseModel, model_validator
from app.schemas.user import UserSummary


class LoginRequest(BaseModel):
    identifier: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.identifier:
            self.identifier = self.username or self.email
        if not self.identifier:
            raise ValueError("Either 'identifier', 'username', or 'email' must be provided.")
        return self


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary
    permissions: List[str]


class ReauthRequest(BaseModel):
    password: str


class ReauthResponse(BaseModel):
    success: bool
    message: str
    reauthenticated_at: str


class TokenData(BaseModel):
    sub: str
    username: str
    role: str
    iat: Optional[int] = None
    exp: Optional[int] = None
