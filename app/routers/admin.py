from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db, User, Usage

router = APIRouter(prefix="/api/admin")


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.tier != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


class UpgradeRequest(BaseModel):
    user_id: int
    tier: str


@router.get("/users")
async def list_users(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "tier": u.tier,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.post("/upgrade")
async def upgrade_user(
    req: UpgradeRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if req.tier not in ("free", "vip", "admin"):
        raise HTTPException(status_code=400, detail="无效的用户等级")

    target = db.query(User).filter(User.id == req.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    target.tier = req.tier
    db.commit()

    return {"success": True, "message": f"用户 {target.username} 已升级为 {req.tier}"}


@router.get("/stats")
async def get_stats(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar()
    free_users = db.query(func.count(User.id)).filter(User.tier == "free").scalar()
    vip_users = db.query(func.count(User.id)).filter(User.tier == "vip").scalar()
    admin_users = db.query(func.count(User.id)).filter(User.tier == "admin").scalar()
    total_analyses = db.query(func.count(Usage.id)).scalar()

    # Analyses per skill
    skill_stats = (
        db.query(Usage.skill_type, func.count(Usage.id))
        .group_by(Usage.skill_type)
        .all()
    )

    return {
        "total_users": total_users,
        "free_users": free_users,
        "vip_users": vip_users,
        "admin_users": admin_users,
        "total_analyses": total_analyses,
        "skill_stats": {s: c for s, c in skill_stats},
    }
