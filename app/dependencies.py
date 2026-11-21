from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

def get_current_user(x_user_id: str | None = Header(default=None, alias="X-User-Id"),
                     db: Session = Depends(get_db)) -> User:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    user = db.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail=f"Unknown user: {x_user_id}")
    return user

def require_role(user: User, role: str):
    if role not in user.roles:
        raise HTTPException(status_code=403, detail=f"{role} role is required")
