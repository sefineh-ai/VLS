from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional
from app.core.config import get_settings
from jose import JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import User
from app.db.session import SessionLocal
from app.models.user import UserRole
from app.core.redis import redis_client
import secrets

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# Password hashing

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT creation

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# JWT decode/validation can be added as needed 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user 

def require_role(role: UserRole):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail=f"Requires {role} role")
        return current_user
    return role_checker

def require_roles(roles: list[UserRole]):
    def roles_checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of roles: {roles}")
        return current_user
    return roles_checker 

REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_refresh_token(email: str) -> str:
    refresh_token = secrets.token_urlsafe(32)
    redis_client.set(f"refresh_token:{refresh_token}", email, ex=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
    return refresh_token

def verify_refresh_token(refresh_token: str) -> str:
    email = redis_client.get(f"refresh_token:{refresh_token}")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return email

def revoke_refresh_token(refresh_token: str):
    redis_client.delete(f"refresh_token:{refresh_token}") 