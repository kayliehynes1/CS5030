"""
Authentication utilities for JWT token generation and verification
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel, field_validator

from fastapi import Header, HTTPException

# Hash password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8') 

# Verify entered password
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# JWT Configuration
SECRET_KEY = "e4f74bcdfe738228d50bd9247cfa11a242e9d5f43a1766b8e16a27c439ba33f0"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenData(BaseModel):
    # Data stored in JWT token
    user_id: int
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    # Login response with token and user info
    token: str
    user: dict

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v) > 100:
            raise ValueError("Name must be less than 100 characters")
        if len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(v) > 50:
            raise ValueError("Password must be less than 50 characters")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if len(v) > 50:
            raise ValueError("Email must be less than 50 characters")
        if '@' not in v or '.' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()



def get_current_user(authorization: str = Header(None)):

    from .data import USERS
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    token_data = verify_token(token)

    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Match token to a real user
    for user in USERS:
        if user.id == token_data.user_id and user.email == token_data.email:
            return user

    raise HTTPException(status_code=401, detail="User not found")

# Create a JWT access token
def create_access_token(user_id, email):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "user_id": user_id,
        "email": email,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify a JWT token and extract user data
def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            return None
            
        return TokenData(user_id=user_id, email=email)
        
    except JWTError:
        return None