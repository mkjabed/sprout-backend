from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from dependencies import get_current_guardian
from models import Guardian, Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    child_id: str
    title: str
    description: str | None = None
    task_type: str  # must_do or optional
    points: int | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

@router.post("")
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    if payload.task_type not in ["must_do", "optional"]:
        raise HTTPException(status_code=400, detail="task_type must be must_do or optional")

    points = payload.points if payload.points else (10 if payload.task_type == "must_do" else 5)

    task = Task(
        guardian_id=current_guardian.id,
        child_id=payload.child_id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        points=points
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "id": str(task.id),
        "title": task.title,
        "task_type": task.task_type,
        "points": task.points,
        "is_active": task.is_active
    }

@router.get("/{child_id}")
def get_tasks(
    child_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    tasks = db.query(Task).filter(
        Task.child_id == child_id,
        Task.guardian_id == current_guardian.id
    ).all()

    return [
        {
            "id": str(t.id),
            "title": t.title,
            "task_type": t.task_type,
            "points": t.points,
            "is_active": t.is_active
        }
        for t in tasks
    ]

@router.put("/{task_id}")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.guardian_id == current_guardian.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.title: task.title = payload.title
    if payload.description: task.description = payload.description

    db.commit()
    return {"message": "Task updated"}

@router.patch("/{task_id}/toggle")
def toggle_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.guardian_id == current_guardian.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_active = not task.is_active
    db.commit()
    return {"message": f"Task {'activated' if task.is_active else 'deactivated'}"}
