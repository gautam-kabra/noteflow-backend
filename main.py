"""
📝 Notes App - Backend API Server
A multi-user notes service with authentication, CRUD operations,
note sharing, labels, pinning, search, and pagination.

Built with FastAPI + SQLAlchemy + JWT Authentication.
"""

import math
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import engine, get_db, Base
from models import User, Note, NoteShare
from schemas import (
    UserRegister, UserLogin, TokenResponse, MessageResponse,
    NoteCreate, NoteUpdate, NoteResponse, PaginatedNotesResponse,
    NoteShareRequest, AboutResponse, NoteLockRequest, NoteUnlockRequest,
    NoteVerifyRequest
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)


# ─── Application Lifecycle ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


# ─── FastAPI App ─────────────────────────────────────────────────────

app = FastAPI(
    title="📝 Notes API",
    description=(
        "A powerful multi-user notes service with JWT authentication, "
        "note sharing, labels, pinning, full-text search, and pagination. "
        "Built for the Backend Engineering Assignment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════
#  AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse,
          tags=["Authentication"])
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Must be a valid email address
    - **password**: Must be at least 6 characters
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully"}


@app.post("/login", response_model=TokenResponse, tags=["Authentication"])
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT access token.
    
    - **email**: Registered email address
    - **password**: Account password
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password"}
        )
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return {"access_token": access_token}


# ═══════════════════════════════════════════════════════════════════════
#  NOTES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/notes", response_model=PaginatedNotesResponse, tags=["Notes"])
def get_all_notes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    label: Optional[str] = Query(None, description="Filter by label"),
    pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    shared_only: Optional[bool] = Query(None, description="Filter by shared status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notes for the authenticated user with pagination.
    
    Supports filtering by label and pinned status.
    Pinned notes are returned first by default.
    """
    # Base query: user's own notes + notes shared with them
    shared_note_ids = db.query(NoteShare.note_id).filter(
        NoteShare.shared_with_user_id == current_user.id
    ).scalar_subquery()
    
    if shared_only:
        query = db.query(Note).filter(Note.id.in_(shared_note_ids))
    else:
        query = db.query(Note).filter(
            or_(
                Note.owner_id == current_user.id,
                Note.id.in_(shared_note_ids)
            )
        )
    
    # Apply filters
    if label is not None:
        query = query.filter(Note.label == label)
    if pinned is not None:
        query = query.filter(Note.is_pinned == pinned)
    
    # Get total count
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    # Order: pinned first, then by updated_at descending
    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    
    # Paginate
    notes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Populate owner email and Mask content for locked notes
    for note in notes:
        note.owner_email = note.owner.email
        if note.is_locked:
            note.content = "•••••••• (Protected Content)"

    return {
        "notes": notes,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


@app.get("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
def get_note_by_id(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific note by its ID.
    
    User can only access their own notes or notes shared with them.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Check access: owner or shared with
    if note.owner_id != current_user.id:
        shared = db.query(NoteShare).filter(
            NoteShare.note_id == note_id,
            NoteShare.shared_with_user_id == current_user.id
        ).first()
        if not shared:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this note"
            )
    
    # Populate owner email
    note.owner_email = note.owner.email

    # Mask content if locked
    if note.is_locked:
        note_data = NoteResponse.model_validate(note)
        note_data.content = "•••••••• (Protected Content)"
        return note_data

    return note


@app.post("/notes", status_code=status.HTTP_201_CREATED, response_model=NoteResponse,
          tags=["Notes"])
def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new note for the authenticated user.
    
    - **title**: Note title (1-500 characters)
    - **content**: Note content
    - **label**: Optional label/tag for categorization
    - **is_pinned**: Optional, pin this note to top
    """
    new_note = Note(
        title=note_data.title,
        content=note_data.content,
        label=note_data.label,
        is_pinned=note_data.is_pinned or False,
        owner_id=current_user.id,
        is_locked=note_data.is_locked or False,
        hashed_lock_password=hash_password(note_data.lock_password) if note_data.lock_password else None
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    return new_note


@app.put("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing note. Only the note owner can update it.
    
    All fields are optional - only provided fields will be updated.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notes"
        )
    
    # Update only provided fields
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["lock_password", "is_locked"]:
            setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Notes"])
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a note. Only the note owner can delete it.
    
    All shares associated with this note will also be removed.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notes"
        )
    
    db.delete(note)
    db.commit()
    
    return None


@app.post("/notes/{note_id}/verify-lock", response_model=NoteResponse, tags=["Notes"])
def verify_note_lock(
    note_id: str,
    verify_data: NoteVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify password for a locked note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check access (owner or shared)
    if note.owner_id != current_user.id:
        shared = db.query(NoteShare).filter(
            NoteShare.note_id == note_id,
            NoteShare.shared_with_user_id == current_user.id
        ).first()
        if not shared:
            raise HTTPException(status_code=403, detail="Access denied")

    if not note.is_locked:
        return {"message": "Note is not locked"}
    
    if not verify_password(verify_data.password, note.hashed_lock_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    # Return the real content only after verification
    return NoteResponse.model_validate(note)


@app.post("/notes/{note_id}/lock", response_model=NoteResponse, tags=["Notes"])
def lock_note(
    note_id: str,
    lock_data: NoteLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lock a note with a password."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can lock the note")
    
    note.is_locked = True
    note.hashed_lock_password = hash_password(lock_data.password)
    db.commit()
    db.refresh(note)
    return note


@app.post("/notes/{note_id}/unlock", response_model=NoteResponse, tags=["Notes"])
def unlock_note(
    note_id: str,
    unlock_data: NoteUnlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently unlock a note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can unlock the note")
    
    if not verify_password(unlock_data.password, note.hashed_lock_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    note.is_locked = False
    note.hashed_lock_password = None
    db.commit()
    db.refresh(note)
    return note


# ═══════════════════════════════════════════════════════════════════════
#  SHARING ENDPOINT
# ═══════════════════════════════════════════════════════════════════════

@app.post("/notes/{note_id}/share", response_model=MessageResponse, tags=["Sharing"])
def share_note(
    note_id: str,
    share_data: NoteShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Share a note with another registered user.
    
    - Only the note owner can share it
    - Cannot share with yourself
    - The shared user will be able to view the note via GET /notes/{id}
    """
    # Verify note exists and belongs to current user
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only share your own notes"
        )
    
    # Find the user to share with
    share_user = db.query(User).filter(User.email == share_data.share_with_email).first()
    
    if not share_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with the provided email"
        )
    
    if share_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot share a note with yourself"
        )
    
    # Check if already shared
    existing_share = db.query(NoteShare).filter(
        NoteShare.note_id == note_id,
        NoteShare.shared_with_user_id == share_user.id
    ).first()
    
    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note is already shared with this user"
        )
    
    # Create the share
    new_share = NoteShare(
        note_id=note_id,
        shared_with_user_id=share_user.id
    )
    db.add(new_share)
    db.commit()
    
    return {"message": f"Note shared successfully with {share_data.share_with_email}"}


# ═══════════════════════════════════════════════════════════════════════
#  SEARCH ENDPOINT (Stretch Goal)
# ═══════════════════════════════════════════════════════════════════════

@app.get("/search", response_model=PaginatedNotesResponse, tags=["Search"])
def search_notes(
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search across note titles and content.
    
    Searches only within the authenticated user's notes (owned + shared).
    """
    search_term = f"%{q}%"
    
    # Get shared note IDs
    shared_note_ids = db.query(NoteShare.note_id).filter(
        NoteShare.shared_with_user_id == current_user.id
    ).scalar_subquery()
    
    query = db.query(Note).filter(
        or_(
            Note.owner_id == current_user.id,
            Note.id.in_(shared_note_ids)
        ),
        or_(
            Note.title.ilike(search_term),
            Note.content.ilike(search_term),
            Note.label.ilike(search_term)
        )
    )
    
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())\
                  .offset((page - 1) * per_page).limit(per_page).all()
    
    # Mask content for locked notes and populate owner email
    for note in notes:
        note.owner_email = note.owner.email
        if note.is_locked:
            note.content = "•••••••• (Protected Content)"
            
    return {
        "notes": notes,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


# ═══════════════════════════════════════════════════════════════════════
#  ABOUT & HEALTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@app.get("/about", tags=["Info"])
def about():
    """
    Returns information about the developer and custom features.
    """
    return {
        "name": "Kabra Gautam",
        "email": "kabragautam007@gmail.com",
        "my features": {
            "NoteFlow Vault": "Provides secondary encryption for individual notes. Content is masked at the API level until verified with a specific password, ensuring sensitive data remains private even if a device is left logged in."
        }
    }


@app.get("/health", tags=["Info"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "Notes API"}


# ─── Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
