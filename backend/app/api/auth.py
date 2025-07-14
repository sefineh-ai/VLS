from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.models import User, UserRole
from app.services.auth import hash_password, verify_password, create_access_token, get_current_user, require_role, create_refresh_token, verify_refresh_token, revoke_refresh_token
from app.db.session import SessionLocal
from sqlalchemy.exc import IntegrityError
from app.services import security
from app.services.security import validate_password_complexity, log_auth_event

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        validate_password_complexity(user_in.password)
    except ValueError as e:
        log_auth_event("register_failed", user_in.email, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        log_auth_event("register_failed", user_in.email, "Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        is_active=True,
        is_superuser=user_in.is_superuser
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        log_auth_event("register_failed", user_in.email, "Registration failed")
        raise HTTPException(status_code=400, detail="Registration failed")
    log_auth_event("register_success", user_in.email)
    # Issue tokens on registration
    access_token = create_access_token({"sub": db_user.email, "role": db_user.role})
    refresh_token = create_refresh_token(db_user.email)
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/login")
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    if security.is_account_locked(user_in.email):
        log_auth_event("login_lockout", user_in.email, "Account locked")
        raise HTTPException(status_code=403, detail="Account is temporarily locked due to too many failed login attempts. Please try again later.")
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        security.increment_failed_attempts(user_in.email)
        log_auth_event("login_failed", user_in.email, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    security.reset_failed_attempts(user_in.email)
    access_token = create_access_token({"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(user.email)
    log_auth_event("login_success", user.email)
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/refresh")
def refresh_token(refresh_token: str = Body(..., embed=True)):
    email = verify_refresh_token(refresh_token)
    access_token = create_access_token({"sub": email})
    log_auth_event("refresh_token", email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(refresh_token: str = Body(..., embed=True)):
    email = verify_refresh_token(refresh_token)
    revoke_refresh_token(refresh_token)
    log_auth_event("logout", email)
    return {"msg": "Logged out"}

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin-only", response_model=UserRead)
def admin_only(current_user: User = Depends(require_role(UserRole.admin))):
    return current_user

@router.get("/streamer-only", response_model=UserRead)
def streamer_only(current_user: User = Depends(require_role(UserRole.streamer))):
    return current_user 