from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from dependencies import get_current_guardian
from models import Guardian, Child, Streak

router = APIRouter(prefix="/children", tags=["children"])

class ChildCreate(BaseModel):
    name: str
    grade: int
    age: int

class ChildUpdate(BaseModel):
    name: str | None = None
    grade: int | None = None
    age: int | None = None

@router.post("")
def create_child(
    payload: ChildCreate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    child = Child(
        guardian_id=current_guardian.id,
        name=payload.name,
        grade=payload.grade,
        age=payload.age
    )
    db.add(child)
    db.commit()
    db.refresh(child)

    # Create streak record for child
    streak = Streak(child_id=child.id)
    db.add(streak)
    db.commit()

    return {
        "id": str(child.id),
        "name": child.name,
        "grade": child.grade,
        "age": child.age,
        "total_points": child.total_points
    }

@router.get("")
def get_children(
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    children = db.query(Child).filter(Child.guardian_id == current_guardian.id).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "grade": c.grade,
            "age": c.age,
            "total_points": c.total_points
        }
        for c in children
    ]

@router.put("/{child_id}")
def update_child(
    child_id: str,
    payload: ChildUpdate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.guardian_id == current_guardian.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if payload.name: child.name = payload.name
    if payload.grade: child.grade = payload.grade
    if payload.age: child.age = payload.age

    db.commit()
    db.refresh(child)
    return {"message": "Child updated", "name": child.name}