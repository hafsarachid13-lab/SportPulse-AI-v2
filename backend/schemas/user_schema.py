from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
	email: EmailStr
	username: str | None = Field(default=None, min_length=3, max_length=100)
	role: Literal["admin", "journaliste"] = "journaliste"
	password: str | None = Field(default=None, min_length=6)
	is_active: bool = True


class UserResponse(BaseModel):
	id: int
	username: str
	email: str
	role: Literal["admin", "journaliste"]
	is_active: bool
	created_at: datetime | None = None
	last_login: datetime | None = None
	email_sent: bool = False
	generated_password: str | None = None


class UserImportResult(BaseModel):
	imported_count: int
	skipped_count: int
	email_sent_count: int
	users: list[UserResponse]
	message: str


class UserPasswordUpdateRequest(BaseModel):
	password: str = Field(min_length=6)


class UserStatusUpdateRequest(BaseModel):
	is_active: bool


class UserActionResult(BaseModel):
	message: str
	user: UserResponse | None = None

