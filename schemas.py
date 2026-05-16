"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ─── User Schemas ────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., description="User password")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ─── Note Schemas ────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    title: str = Field(..., max_length=500, description="Note title")
    content: str = Field(..., description="Note content")
    label: Optional[str] = Field(None, max_length=100, description="Optional label/tag")
    is_pinned: Optional[bool] = Field(False, description="Pin this note")
    is_locked: Optional[bool] = Field(False, description="Lock this note with a password")
    lock_password: Optional[str] = Field(None, description="Password to lock the note")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None)
    label: Optional[str] = Field(None, max_length=100)
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None
    lock_password: Optional[str] = None


class NoteResponse(BaseModel):
    """Schema for note response."""
    id: str
    title: str
    content: str
    label: Optional[str] = None
    is_pinned: bool = False
    is_locked: bool = False
    owner_id: str
    owner_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedNotesResponse(BaseModel):
    """Schema for paginated notes list."""
    notes: List[NoteResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ─── Share Schemas ───────────────────────────────────────────────────

class NoteShareRequest(BaseModel):
    """Schema for sharing a note."""
    share_with_email: EmailStr


class NoteLockRequest(BaseModel):
    """Schema for locking a note."""
    password: str = Field(..., min_length=1)


class NoteUnlockRequest(BaseModel):
    """Schema for unlocking (permanently removing lock) a note."""
    password: str


class NoteVerifyRequest(BaseModel):
    """Schema for verifying password to view a locked note."""
    password: str


# ─── About Schema ───────────────────────────────────────────────────

class AboutResponse(BaseModel):
    """Schema for about endpoint."""
    name: str
    email: str
    my_features: dict
