import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import models, security
from .database import get_db


def get_token_from_header(authorization: str = Header(None)) -> str:
    """Достаёт токен из заголовка Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Не авторизован: отсутствует токен")
    return authorization.split(" ", 1)[1]


def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> models.User:
    """Определяет текущего пользователя по JWT-токену.
    401 — если токена нет / он невалиден / истёк / отозван / пользователь неактивен."""
    try:
        payload = security.decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк, войдите заново")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    jti = payload.get("jti")
    if db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Токен отозван, требуется повторный вход")

    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь не найден или деактивирован")

    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """403, если роль пользователя не 'admin'."""
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user


def get_rule(db: Session, role_id: int, element_name: str) -> models.AccessRule | None:
    """Возвращает правило доступа роли к элементу приложения (или None, если правила нет)."""
    element = db.query(models.BusinessElement).filter(models.BusinessElement.name == element_name).first()
    if not element:
        return None
    return (
        db.query(models.AccessRule)
        .filter(models.AccessRule.role_id == role_id, models.AccessRule.element_id == element.id)
        .first()
    )
