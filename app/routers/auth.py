from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db
from ..dependencies import get_current_user, get_token_from_header

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


def _to_user_out(user: models.User) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id,
        last_name=user.last_name,
        first_name=user.first_name,
        middle_name=user.middle_name,
        email=user.email,
        role=user.role.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    if data.password != data.password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    default_role = db.query(models.Role).filter(models.Role.name == "user").first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Роль 'user' не сконфигурирована. Запустите: python -m app.seed")

    user = models.User(
        last_name=data.last_name,
        first_name=data.first_name,
        middle_name=data.middle_name,
        email=data.email,
        password_hash=security.hash_password(data.password),
        role_id=default_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_out(user)


@router.post("/login", response_model=schemas.TokenOut)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not user.is_active or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = security.create_access_token(user.id)
    return schemas.TokenOut(access_token=token)


@router.post("/logout")
def logout(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)):
    try:
        payload = security.decode_access_token(token)
    except Exception:
        return {"detail": "Сессия уже недействительна"}

    jti = payload.get("jti")
    if jti and not db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
        db.add(models.RevokedToken(jti=jti))
        db.commit()
    return {"detail": "Вы вышли из системы"}


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return _to_user_out(current_user)


@router.patch("/me", response_model=schemas.UserOut)
def update_me(
    data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.email and data.email != current_user.email:
        if db.query(models.User).filter(models.User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email уже занят")
        current_user.email = data.email

    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.middle_name is not None:
        current_user.middle_name = data.middle_name
    if data.password:
        current_user.password_hash = security.hash_password(data.password)

    db.commit()
    db.refresh(current_user)
    return _to_user_out(current_user)


@router.delete("/me")
def delete_me(
    token: str = Depends(get_token_from_header),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Мягкое удаление аккаунта: is_active=False, текущий токен отзывается, logout выполняется автоматически."""
    current_user.is_active = False
    db.commit()

    try:
        payload = security.decode_access_token(token)
        jti = payload.get("jti")
        if jti and not db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
            db.add(models.RevokedToken(jti=jti))
            db.commit()
    except Exception:
        pass

    return {"detail": "Аккаунт деактивирован. Повторный вход невозможен."}
