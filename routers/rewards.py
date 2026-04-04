from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from dependencies import get_current_guardian
from models import Guardian, Child, Reward
from datetime import datetime

router = APIRouter(prefix="/rewards", tags=["rewards"])

class RewardCreate(BaseModel):
    child_id: str
    title: str
    points_required: int

@router.post("")
def create_reward(
    payload: RewardCreate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    reward = Reward(
        guardian_id=current_guardian.id,
        child_id=payload.child_id,
        title=payload.title,
        points_required=payload.points_required
    )
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return {
        "id": str(reward.id),
        "title": reward.title,
        "points_required": reward.points_required,
        "is_delivered": reward.is_delivered
    }

@router.get("/{child_id}")
def get_rewards(
    child_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    child = db.query(Child).filter(Child.id == child_id).first()
    rewards = db.query(Reward).filter(
        Reward.child_id == child_id,
        Reward.is_active == True
    ).all()

    return [
        {
            "id": str(r.id),
            "title": r.title,
            "points_required": r.points_required,
            "current_points": child.total_points,
            "points_remaining": max(0, r.points_required - child.total_points),
            "is_delivered": r.is_delivered,
            "unlocked": child.total_points >= r.points_required
        }
        for r in rewards
    ]

@router.patch("/{reward_id}/deliver")
def deliver_reward(
    reward_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian)
):
    reward = db.query(Reward).filter(
        Reward.id == reward_id,
        Reward.guardian_id == current_guardian.id
    ).first()
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    reward.is_delivered = True
    reward.is_active = False
    reward.delivered_at = datetime.utcnow()
    db.commit()
    return {"message": "Reward marked as delivered"}