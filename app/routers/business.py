from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, get_rule

router = APIRouter(prefix="/business", tags=["Бизнес-объекты (демо)"])

MOCK_PRODUCTS = [
    {"id": 1, "name": "Ноутбук Lenovo", "price": 55000, "owner_id": 1},
    {"id": 2, "name": "Смартфон Pixel", "price": 30000, "owner_id": 2},
    {"id": 3, "name": "Наушники Sony", "price": 5000, "owner_id": 2},
]

MOCK_STORES = [
    {"id": 1, "name": "Магазин на Невском", "city": "Санкт-Петербург", "owner_id": 1},
    {"id": 2, "name": "Магазин у метро", "city": "Москва", "owner_id": 2},
]

MOCK_ORDERS = [
    {"id": 1, "product_id": 1, "quantity": 1, "owner_id": 3},
    {"id": 2, "product_id": 3, "quantity": 2, "owner_id": 3},
    {"id": 3, "product_id": 2, "quantity": 1, "owner_id": 2},
]


def _check_object_access(
    db: Session,
    current_user: models.User,
    element_name: str,
    action: str,
    obj_owner_id: Optional[int] = None,
):
    """Проверка доступа к ОДНОМУ объекту (read / update / delete).
    Сначала проверяется вариант '..._all' (доступ ко всем объектам),
    затем обычный вариант (доступ только к своим объектам)."""
    rule = get_rule(db, current_user.role_id, element_name)

    all_ok = bool(rule and getattr(rule, f"{action}_all_permission"))
    own_ok = bool(rule and getattr(rule, f"{action}_permission"))

    if all_ok:
        return
    if own_ok and obj_owner_id == current_user.id:
        return
    if own_ok and obj_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён: это не ваш объект")
    raise HTTPException(status_code=403, detail="Доступ запрещён: недостаточно прав")


def _check_create_access(db: Session, current_user: models.User, element_name: str):
    rule = get_rule(db, current_user.role_id, element_name)
    if not (rule and rule.create_permission):
        raise HTTPException(status_code=403, detail="Доступ запрещён: недостаточно прав")


def _scope_list(db: Session, current_user: models.User, element_name: str, items: list) -> list:
    """Список: если есть read_all — отдаём всё, если только read — отдаём только своё."""
    rule = get_rule(db, current_user.role_id, element_name)
    if rule and rule.read_all_permission:
        return items
    if rule and rule.read_permission:
        return [i for i in items if i["owner_id"] == current_user.id]
    raise HTTPException(status_code=403, detail="Доступ запрещён: недостаточно прав")


def _find_or_404(items: list, item_id: int) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Объект не найден")


@router.get("/products")
def list_products(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _scope_list(db, current_user, "products", MOCK_PRODUCTS)


@router.get("/products/{product_id}")
def get_product(product_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = _find_or_404(MOCK_PRODUCTS, product_id)
    _check_object_access(db, current_user, "products", "read", product["owner_id"])
    return product


@router.post("/products", status_code=201)
def create_product(name: str, price: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_create_access(db, current_user, "products")
    new_id = max((p["id"] for p in MOCK_PRODUCTS), default=0) + 1
    product = {"id": new_id, "name": name, "price": price, "owner_id": current_user.id}
    MOCK_PRODUCTS.append(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = _find_or_404(MOCK_PRODUCTS, product_id)
    _check_object_access(db, current_user, "products", "delete", product["owner_id"])
    MOCK_PRODUCTS.remove(product)
    return {"detail": "Товар удалён"}



@router.get("/stores")
def list_stores(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _scope_list(db, current_user, "stores", MOCK_STORES)


@router.get("/stores/{store_id}")
def get_store(store_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    store = _find_or_404(MOCK_STORES, store_id)
    _check_object_access(db, current_user, "stores", "read", store["owner_id"])
    return store


@router.get("/orders")
def list_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _scope_list(db, current_user, "orders", MOCK_ORDERS)


@router.get("/orders/{order_id}")
def get_order(order_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = _find_or_404(MOCK_ORDERS, order_id)
    _check_object_access(db, current_user, "orders", "read", order["owner_id"])
    return order


@router.post("/orders", status_code=201)
def create_order(
    product_id: int,
    quantity: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_create_access(db, current_user, "orders")
    new_id = max((o["id"] for o in MOCK_ORDERS), default=0) + 1
    order = {"id": new_id, "product_id": product_id, "quantity": quantity, "owner_id": current_user.id}
    MOCK_ORDERS.append(order)
    return order


@router.delete("/orders/{order_id}")
def delete_order(order_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = _find_or_404(MOCK_ORDERS, order_id)
    _check_object_access(db, current_user, "orders", "delete", order["owner_id"])
    MOCK_ORDERS.remove(order)
    return {"detail": "Заказ удалён"}


@router.get("/users", response_model=List[schemas.UserOut])
def list_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = get_rule(db, current_user.role_id, "users")
    if rule and rule.read_all_permission:
        users = db.query(models.User).all()
    elif rule and rule.read_permission:
        users = [current_user]
    else:
        raise HTTPException(status_code=403, detail="Доступ запрещён: недостаточно прав")

    return [
        schemas.UserOut(
            id=u.id,
            last_name=u.last_name,
            first_name=u.first_name,
            middle_name=u.middle_name,
            email=u.email,
            role=u.role.name,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]
