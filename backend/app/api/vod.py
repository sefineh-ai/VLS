from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import SessionLocal
from app.models import VOD, User, UserRole, Stream
from app.schemas.vod import VODRead
from app.services.auth import get_current_user

router = APIRouter(prefix="/vods", tags=["vods"])

VOD_BASE_URL = "http://localhost:8080/recordings"  # Adjust for prod/cloud

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[VODRead])
def list_vods(
    db: Session = Depends(get_db),
    is_public: Optional[bool] = Query(None),
    owner_id: Optional[int] = Query(None)
):
    query = db.query(VOD)
    if is_public is not None:
        query = query.filter(VOD.is_public == is_public)
    if owner_id:
        query = query.join(Stream).filter(Stream.owner_id == owner_id)
    return query.order_by(VOD.created_at.desc()).all()

@router.get("/{vod_id}/playback-url")
def get_vod_playback_url(vod_id: int, db: Session = Depends(get_db)):
    vod = db.query(VOD).filter(VOD.id == vod_id).first()
    if not vod:
        raise HTTPException(status_code=404, detail="VOD not found")
    playback_url = f"{VOD_BASE_URL}/{vod.file_path}"
    return {"playback_url": playback_url}

@router.delete("/{vod_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vod(
    vod_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vod = db.query(VOD).filter(VOD.id == vod_id).first()
    if not vod:
        raise HTTPException(status_code=404, detail="VOD not found")
    stream = db.query(Stream).filter(Stream.id == vod.stream_id).first()
    if stream.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this VOD")
    db.delete(vod)
    db.commit()
    return None 