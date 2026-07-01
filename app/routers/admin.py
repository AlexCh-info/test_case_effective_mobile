from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import require_admin

# Все эндпоинты этого роутера доступны только пользователям с ролью admin
router = APIRouter(prefix="/admin", tags=["Администрирование"], dependencies=[Depends(require_admin)])


@router.get("/roles", response_model=List[schemas.RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).all()


@router.post("/roles", response_model=schemas.RoleOut, status_code=201)
def create_role(data: schemas.RoleCreate, db: Session = Depends(get_db)):
    if db.query(models.Role).filter(models.Role.name == data.name).first():
        raise HTTPException(status_code=400, detail="Роль уже существует")
    role = models.Role(name=data.name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role



@router.get("/business-elements", response_model=List[schemas.BusinessElementOut])
def list_elements(db: Session = Depends(get_db)):
    return db.query(models.BusinessElement).all()


@router.post("/business-elements", response_model=schemas.BusinessElementOut, status_code=201)
def create_element(data: schemas.BusinessElementCreate, db: Session = Depends(get_db)):
    if db.query(models.BusinessElement).filter(models.BusinessElement.name == data.name).first():
        raise HTTPException(status_code=400, detail="Элемент уже существует")
    element = models.BusinessElement(name=data.name, description=data.description)
    db.add(element)
    db.commit()
    db.refresh(element)
    return element



@router.get("/access-rules", response_model=List[schemas.AccessRuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.query(models.AccessRule).all()


@router.post("/access-rules", response_model=schemas.AccessRuleOut, status_code=201)
def upsert_rule(data: schemas.AccessRuleUpsert, db: Session = Depends(get_db)):
    """Создаёт правило для пары (роль, элемент), либо обновляет существующее."""
    if not db.query(models.Role).filter(models.Role.id == data.role_id).first():
        raise HTTPException(status_code=404, detail="Роль не найдена")
    if not db.query(models.BusinessElement).filter(models.BusinessElement.id == data.element_id).first():
        raise HTTPException(status_code=404, detail="Элемент приложения не найден")

    rule = (
        db.query(models.AccessRule)
        .filter(models.AccessRule.role_id == data.role_id, models.AccessRule.element_id == data.element_id)
        .first()
    )
    if rule is None:
        rule = models.AccessRule(role_id=data.role_id, element_id=data.element_id)
        db.add(rule)

    for field in (
        "read_permission",
        "read_all_permission",
        "create_permission",
        "update_permission",
        "update_all_permission",
        "delete_permission",
        "delete_all_permission",
    ):
        setattr(rule, field, getattr(data, field))

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/access-rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.AccessRule).filter(models.AccessRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    db.delete(rule)
    db.commit()
    return {"detail": "Правило удалено"}
