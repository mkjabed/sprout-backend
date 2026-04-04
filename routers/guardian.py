from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_guardian
from models import Guardian

router = APIRouter(prefix="/guardian", tags=["guardian"])

@router.get("/me")
def get_me(current_guardian: Guardian = Depends(get_current_guardian)):
    return {
        "id": str(current_guardian.id),
        "name": current_guardian.name,
        "email": current_guardian.email,
        "timezone": current_guardian.timezone
    }