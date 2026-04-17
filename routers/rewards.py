from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_guardian, get_current_guardian_optional
from models import Child, Guardian, Reward

router = APIRouter(prefix="/rewards", tags=["rewards"])


class RewardCreate(BaseModel):
    child_id: str
    title: str
    points_required: int


@router.post("")
def create_reward(
    payload: RewardCreate,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian),
):
    reward = Reward(
        guardian_id=current_guardian.id,
        child_id=payload.child_id,
        title=payload.title,
        points_required=payload.points_required,
    )
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return {
        "id": str(reward.id),
        "title": reward.title,
        "points_required": reward.points_required,
        "is_delivered": reward.is_delivered,
    }


@router.get("/{child_id}")
def get_rewards(
    child_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian | None = Depends(get_current_guardian_optional),
):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if current_guardian and str(child.guardian_id) != str(current_guardian.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this child")

    rewards = db.query(Reward).filter(Reward.child_id == child_id, Reward.is_active.is_(True)).all()

    return [
        {
            "id": str(reward.id),
            "title": reward.title,
            "points_required": reward.points_required,
            "current_points": child.total_points,
            "points_remaining": max(0, reward.points_required - child.total_points),
            "is_delivered": reward.is_delivered,
            "unlocked": child.total_points >= reward.points_required,
        }
        for reward in rewards
    ]


@router.patch("/{reward_id}/deliver")
def deliver_reward(
    reward_id: str,
    db: Session = Depends(get_db),
    current_guardian: Guardian = Depends(get_current_guardian),
):
    reward = (
        db.query(Reward)
        .filter(Reward.id == reward_id, Reward.guardian_id == current_guardian.id)
        .first()
    )
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    reward.is_delivered = True
    reward.is_active = False
    reward.delivered_at = datetime.utcnow()
    db.commit()
    return {"message": "Reward marked as delivered"}
