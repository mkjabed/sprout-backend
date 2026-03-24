from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from database import get_db
from models import Guardian
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


# --- Pydantic Schemas ---

class GuardianSignup(BaseModel):
    name: str
    email: EmailStr
    pin: str

class GuardianLogin(BaseModel):
    email: EmailStr
    pin: str


# --- Helper Functions ---

def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    return pwd_context.verify(plain_pin, hashed_pin)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Routes ---

@router.post("/signup")
def signup(payload: GuardianSignup, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(Guardian).filter(Guardian.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate PIN is 4 digits
    if len(payload.pin) != 4 or not payload.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")

    # Create guardian
    guardian = Guardian(
        name=payload.name,
        email=payload.email,
        pin_hash=hash_pin(payload.pin)
    )
    db.add(guardian)
    db.commit()
    db.refresh(guardian)

    token = create_access_token({"sub": str(guardian.id)})

    return {
        "message": "Account created successfully",
        "token": token,
        "guardian": {
            "id": str(guardian.id),
            "name": guardian.name,
            "email": guardian.email
        }
    }


@router.post("/login")
def login(payload: GuardianLogin, db: Session = Depends(get_db)):
    guardian = db.query(Guardian).filter(Guardian.email == payload.email).first()

    if not guardian:
        raise HTTPException(status_code=401, detail="Invalid email or PIN")

    if not verify_pin(payload.pin, guardian.pin_hash):
        raise HTTPException(status_code=401, detail="Invalid email or PIN")

    token = create_access_token({"sub": str(guardian.id)})

    return {
        "message": "Login successful",
        "token": token,
        "guardian": {
            "id": str(guardian.id),
            "name": guardian.name,
            "email": guardian.email
        }
    }