from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_guardian_optional
from models import Child, DailyLog, Guardian, Streak, Task

router = APIRouter(prefix="/daily", tags=["daily"])


def check_and_update_streak(child_id, db: Session):
    streak = db.query(Streak).filter(Streak.child_id == child_id).first()
    child = db.query(Child).filter(Child.id == child_id).first()
    today = date.today()

    must_do_tasks = (
        db.query(Task)
        .filter(Task.child_id == child_id, Task.task_type == "must_do", Task.is_active.is_(True))
        .all()
    )

    if not must_do_tasks or not streak or not child:
        return

    must_do_ids = [task.id for task in must_do_tasks]
    completed_today = (
        db.query(DailyLog)
        .filter(
            DailyLog.child_id == child_id,
            DailyLog.log_date == today,
            DailyLog.task_id.in_(must_do_ids),
            DailyLog.completed.is_(True),
        )
        .count()
    )

    all_done = completed_today == len(must_do_ids)

    if all_done and streak.last_completed_date != today:
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        streak.last_completed_date = today
        streak.updated_at = datetime.utcnow()
        db.commit()


def get_child_or_404(child_id: str, db: Session):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


def serialize_log(log: DailyLog, task: Task):
    return {
        "log_id": str(log.id),
        "task_id": str(task.id),
        "title": task.title,
        "task_type": task.task_type,
        "points": task.points,
        "completed": log.completed,
        "points_earned": log.points_earned,
    }


@router.get("/{child_id}")
def get_daily_tasks(
    child_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian | None = Depends(get_current_guardian_optional),
):
    today = date.today()
    child = get_child_or_404(child_id, db)

    if current_guardian and str(child.guardian_id) != str(current_guardian.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this child")

    logs = (
        db.query(DailyLog)
        .filter(DailyLog.child_id == child_id, DailyLog.log_date == today)
        .all()
    )

    if not logs:
        tasks = (
            db.query(Task)
            .filter(Task.child_id == child_id, Task.is_active.is_(True))
            .all()
        )
        for task in tasks:
            db.add(
                DailyLog(
                    child_id=child_id,
                    task_id=task.id,
                    log_date=today,
                    completed=False,
                    points_earned=0,
                )
            )
        db.commit()
        logs = (
            db.query(DailyLog)
            .filter(DailyLog.child_id == child_id, DailyLog.log_date == today)
            .all()
        )

    streak = db.query(Streak).filter(Streak.child_id == child.id).first()
    task_map = {
        task.id: task
        for task in db.query(Task).filter(Task.id.in_([log.task_id for log in logs])).all()
    }
    serialized_logs = [
        serialize_log(log, task_map[log.task_id])
        for log in logs
        if log.task_id in task_map
    ]

    return {
        "child_id": str(child.id),
        "child_name": child.name,
        "child": {
            "id": str(child.id),
            "name": child.name,
            "grade": child.grade,
            "age": child.age,
            "total_points": child.total_points,
        },
        "date": today.isoformat(),
        "streak": streak.current_streak if streak else 0,
        "total_points": sum(log["points_earned"] for log in serialized_logs),
        "logs": serialized_logs,
    }


@router.post("/{log_id}/complete")
def complete_task(log_id: str, db: Session = Depends(get_db)):
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    if log.completed:
        raise HTTPException(status_code=400, detail="Task already completed")

    task = db.query(Task).filter(Task.id == log.task_id).first()
    child = db.query(Child).filter(Child.id == log.child_id).first()
    if not task or not child:
        raise HTTPException(status_code=404, detail="Task or child not found")

    log.completed = True
    log.completed_at = datetime.utcnow()
    log.points_earned = task.points
    child.total_points += task.points

    db.commit()
    check_and_update_streak(log.child_id, db)

    streak = db.query(Streak).filter(Streak.child_id == child.id).first()

    return {
        "message": "Task completed",
        "points_earned": task.points,
        "total_points": child.total_points,
        "streak": streak.current_streak if streak else 0,
        "child_name": child.name,
    }
