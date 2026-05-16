"""
SQLAlchemy ORM Models for the Notes application.
Defines User, Note, NoteShare, and NoteLabel tables.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Table, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
import uuid

from database import Base


def generate_uuid():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and note ownership."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    shared_notes = relationship("NoteShare", back_populates="shared_with_user",
                                foreign_keys="NoteShare.shared_with_user_id")

    def __repr__(self):
        return f"<User(email={self.email})>"


class Note(Base):
    """Note model with support for labels and sharing."""
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False)
    label = Column(String(100), nullable=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_locked = Column(Boolean, default=False)
    hashed_lock_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="notes")
    shared_with = relationship("NoteShare", back_populates="note",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Note(title={self.title}, owner={self.owner_id})>"


class NoteShare(Base):
    """
    Association table for note sharing.
    Tracks which notes are shared with which users.
    """
    __tablename__ = "note_shares"

    id = Column(String, primary_key=True, default=generate_uuid)
    note_id = Column(String, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    shared_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint to prevent duplicate shares
    __table_args__ = (
        UniqueConstraint('note_id', 'shared_with_user_id', name='unique_note_share'),
    )

    # Relationships
    note = relationship("Note", back_populates="shared_with")
    shared_with_user = relationship("User", back_populates="shared_notes",
                                    foreign_keys=[shared_with_user_id])

    def __repr__(self):
        return f"<NoteShare(note={self.note_id}, user={self.shared_with_user_id})>"
