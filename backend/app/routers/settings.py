from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(user: User = Depends(get_current_user)):
    return user.settings


@router.patch("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user.settings, field, value)
    db.commit()
    return user.settings
