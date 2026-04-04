from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_guardian
from models import Guardian, Child, Task, DailyLog, Streak
from datetime import date, datetime

router = APIRouter(prefix="/daily", tags=["daily"])

def check_and_update_streak(child_id, db: Session):
    streak = db.query(Streak).filter(Streak.child_id == child_id).first()
    child = db.query(Child).filter(Child.id == child_id).first()
    today = date.today()

    # Get all must_do tasks for child
    must_do_tasks = db.query(Task).filter(
        Task.child_id == child_id,
        Task.task_type == "must_do",
        Task.is_active == True
    ).all()

    if not must_do_tasks:
        return

    must_do_ids = [t.id for t in must_do_tasks]

    # Check if all must_do tasks are completed today
    completed_today = db.query(DailyLog).filter(
        DailyLog.child_id == child_id,
        DailyLog.log_date == today,
        DailyLog.task_id.in_(must_do_ids),
        DailyLog.completed == True
    ).count()

    all_done = completed_today == len(must_do_ids)

    if all_done:
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        streak.last_completed_date = today
        streak.updated_at = datetime.utcnow()
        db.commit()

@router.get("/{child_id}")
def get_daily_tasks(
    child_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    today = date.today()

    logs = db.query(DailyLog).filter(
        DailyLog.child_id == child_id,
        DailyLog.log_date == today
    ).all()

    # If no logs exist for today, create them
    if not logs:
        tasks = db.query(Task).filter(
            Task.child_id == child_id,
            Task.is_active == True
        ).all()
        for task in tasks:
            log = DailyLog(
                child_id=child_id,
                task_id=task.id,
                log_date=today,
                completed=False,
                points_earned=0
            )
            db.add(log)
        db.commit()
        logs = db.query(DailyLog).filter(
            DailyLog.child_id == child_id,
            DailyLog.log_date == today
        ).all()

    result = []
    for log in logs:
        task = db.query(Task).filter(Task.id == log.task_id).first()
        result.append({
            "log_id": str(log.id),
            "task_id": str(task.id),
            "title": task.title,
            "task_type": task.task_type,
            "points": task.points,
            "completed": log.completed,
            "points_earned": log.points_earned
        })

    return result

@router.post("/{log_id}/complete")
def complete_task(
    log_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    if log.completed:
        raise HTTPException(status_code=400, detail="Task already completed")

    task = db.query(Task).filter(Task.id == log.task_id).first()
    child = db.query(Child).filter(Child.id == log.child_id).first()

    log.completed = True
    log.completed_at = datetime.utcnow()
    log.points_earned = task.points
    child.total_points += task.points

    db.commit()

    check_and_update_streak(log.child_id, db)

    return {
        "message": "Task completed",
        "points_earned": task.points,
        "total_points": child.total_points
    }