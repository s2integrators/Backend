# """
# Core authentication helpers for the FastAPI app.

# Provides:
# - hash_password(password: str) -> str
# - verify_password(plain_password: str, hashed_password: str) -> bool
# - create_access_token(data: dict, expires_minutes: int = 60) -> str
# - get_current_user dependency for route protection

# Notes:
# - This implementation uses passlib[bcrypt] for password hashing and python-jose for JWT.
# - If you don't have these libraries installed, `pip install passlib[bcrypt] python-jose[cryptography]`
#   or adapt the functions accordingly.
# """

# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any

# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from passlib.context import CryptContext

# # Secret and algorithm — keep secret in env or config for production
# # Replace with values from app.core.config if you have them centralized
# try:
#     # try to import from your central config
#     from app.core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
# except Exception:
#     SECRET_KEY = "change-me-to-a-long-random-secret"
#     ACCESS_TOKEN_EXPIRE_MINUTES = 60
#     ALGORITHM = "HS256"

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")  # adjust if your login path differs


# def hash_password(password: str) -> str:
#     """Hash a plaintext password."""
#     if password is None:
#         raise ValueError("password must be provided")
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a plaintext password against a hash."""
#     if plain_password is None or hashed_password is None:
#         return False
#     try:
#         return pwd_context.verify(plain_password, hashed_password)
#     except Exception:
#         return False


# def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
#     """
#     Create a JWT access token.
#     `data` should be a dict with identifying claims, e.g. {"sub": "user@example.com", "user_id": 123}
#     """
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire, "iat": datetime.utcnow()})
#     token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return token


# def decode_access_token(token: str) -> Dict[str, Any]:
#     """Decode token, raising HTTPException on failure."""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         # token must be a dict
#         if not isinstance(payload, dict):
#             raise credentials_exception
#         return payload
#     except JWTError:
#         raise credentials_exception


# async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
#     """
#     FastAPI dependency that returns the token payload representing the current user.
#     If you want to load the user object from DB, replace this with a DB lookup using payload['sub'] or user_id.
#     """
#     payload = decode_access_token(token)
#     # Basic validation — ensure we have a subject or user identifier
#     if "sub" not in payload and "user_id" not in payload:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
#     return payload








"""
Core authentication helpers for the FastAPI app.

Provides:
- hash_password(password: str) -> str
- verify_password(plain_password: str, hashed_password: str) -> bool
- create_access_token(data: dict, expires_minutes: int = 60) -> str
- get_current_user dependency for route protection

This version uses pbkdf2_sha256 instead of bcrypt
to avoid Windows bcrypt backend issues and the 72-byte password limit.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load secrets
try:
    from app.core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
except Exception:
    SECRET_KEY = "change-me-to-a-long-random-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    ALGORITHM = "HS256"

# 🔥 Use pbkdf2_sha256 instead of bcrypt
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Token URL expected by OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# -------------------------------
# Password Hashing
# -------------------------------
def hash_password(password: str) -> str:
    if not password:
        raise ValueError("password must be provided")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# -------------------------------
# JWT Handling
# -------------------------------
def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not isinstance(payload, dict):
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# -------------------------------
# Dependency: Get Current User
# -------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    payload = decode_access_token(token)
    if "sub" not in payload and "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return payload
