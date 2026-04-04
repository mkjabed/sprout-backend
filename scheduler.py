from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Child, Task, DailyLog
from datetime import date
import pytz

def reset_daily_tasks():
    db: Session = SessionLocal()
    try:
        today = date.today()
        children = db.query(Child).all()

        for child in children:
            tasks = db.query(Task).filter(
                Task.child_id == child.id,
                Task.is_active == True
            ).all()

            for task in tasks:
                existing = db.query(DailyLog).filter(
                    DailyLog.child_id == child.id,
                    DailyLog.task_id == task.id,
                    DailyLog.log_date == today
                ).first()

                if not existing:
                    log = DailyLog(
                        child_id=child.id,
                        task_id=task.id,
                        log_date=today,
                        completed=False,
                        points_earned=0
                    )
                    db.add(log)

        db.commit()
        print(f"Daily reset done for {today}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        reset_daily_tasks,
        CronTrigger(hour=0, minute=0, timezone=pytz.timezone("Asia/Dhaka"))
    )
    scheduler.start()
    return scheduler