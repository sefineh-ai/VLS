from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.stream import StreamCreate, StreamUpdate, StreamRead
from app.models import Stream, StreamStatus, User, UserRole
from app.db.session import SessionLocal
from app.services.auth import get_current_user, require_roles
import secrets
from app.core.config import get_settings

settings = get_settings()

RTMP_BASE_URL = "rtmp://localhost/live"
HLS_BASE_URL = "http://localhost:8080/hls"

router = APIRouter(prefix="/streams", tags=["streams"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=StreamRead)
def create_stream(
    stream_in: StreamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.streamer, UserRole.admin]))
):
    stream_key = secrets.token_urlsafe(24)
    stream = Stream(
        title=stream_in.title,
        description=stream_in.description,
        is_public=stream_in.is_public,
        stream_key=stream_key,
        owner_id=current_user.id
    )
    db.add(stream)
    db.commit()
    db.refresh(stream)
    return stream

@router.get("/{stream_id}", response_model=StreamRead)
def get_stream(stream_id: int, db: Session = Depends(get_db)):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream

@router.put("/{stream_id}", response_model=StreamRead)
def update_stream(
    stream_id: int,
    stream_in: StreamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if stream.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this stream")
    for field, value in stream_in.dict(exclude_unset=True).items():
        setattr(stream, field, value)
    db.commit()
    db.refresh(stream)
    return stream

@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stream(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if stream.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this stream")
    db.delete(stream)
    db.commit()
    return None

@router.get("/", response_model=List[StreamRead])
def list_streams(
    db: Session = Depends(get_db),
    status: Optional[StreamStatus] = Query(None),
    owner_id: Optional[int] = Query(None),
    is_public: Optional[bool] = Query(None)
):
    query = db.query(Stream)
    if status:
        query = query.filter(Stream.status == status)
    if owner_id:
        query = query.filter(Stream.owner_id == owner_id)
    if is_public is not None:
        query = query.filter(Stream.is_public == is_public)
    return query.order_by(Stream.created_at.desc()).all()

@router.get("/{stream_id}/ingest-url")
def get_ingest_url(stream_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if stream.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to view ingest URL")
    ingest_url = f"{RTMP_BASE_URL}/{stream.stream_key}"
    return {"ingest_url": ingest_url}

@router.get("/{stream_id}/playback-url")
def get_playback_url(stream_id: int, db: Session = Depends(get_db)):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    playback_url = f"{HLS_BASE_URL}/{stream.stream_key}.m3u8"
    return {"playback_url": playback_url}

@router.post("/{stream_id}/status")
def update_stream_status(
    stream_id: int,
    status: StreamStatus = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stream = db.query(Stream).filter(Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    if stream.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to update stream status")
    stream.status = status
    db.commit()
    db.refresh(stream)
    return {"id": stream.id, "status": stream.status}

@router.post("/webhook/stream-start")
async def webhook_stream_start(request: Request, db: Session = Depends(get_db)):
    data = None
    try:
        data = await request.json()
    except Exception:
        data = await request.form()
    stream_key = data.get("name") or data.get("stream_key")
    if not stream_key:
        raise HTTPException(status_code=400, detail="Missing stream_key")
    stream = db.query(Stream).filter(Stream.stream_key == stream_key).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream.status = StreamStatus.live
    db.commit()
    db.refresh(stream)
    return {"id": stream.id, "status": stream.status}

@router.post("/webhook/stream-stop")
async def webhook_stream_stop(request: Request, db: Session = Depends(get_db)):
    data = None
    try:
        data = await request.json()
    except Exception:
        data = await request.form()
    stream_key = data.get("name") or data.get("stream_key")
    if not stream_key:
        raise HTTPException(status_code=400, detail="Missing stream_key")
    stream = db.query(Stream).filter(Stream.stream_key == stream_key).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    stream.status = StreamStatus.ended
    db.commit()
    db.refresh(stream)
    return {"id": stream.id, "status": stream.status} 