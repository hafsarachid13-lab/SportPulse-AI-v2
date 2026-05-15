from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    role: Literal["admin", "journaliste"] = "journaliste"


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    login: str | None = None
    identifier: str | None = None
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Literal["admin", "journaliste"]
    is_active: bool
    last_login: datetime | None = None
