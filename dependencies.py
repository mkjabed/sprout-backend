import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import Guardian

bearer = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


def _decode_guardian_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
        guardian_id = payload.get("sub")
        if not guardian_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    guardian = db.query(Guardian).filter(Guardian.id == guardian_id).first()
    if not guardian:
        raise HTTPException(status_code=401, detail="Guardian not found")

    return guardian


def get_current_guardian(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    return _decode_guardian_from_token(credentials.credentials, db)


def get_current_guardian_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
):
    if not credentials:
        return None

    return _decode_guardian_from_token(credentials.credentials, db)
