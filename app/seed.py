"""
Наполняет базу данных тестовыми данными: роли, элементы приложения,
правила доступа и демо-пользователей (по одному на каждую роль).

Запуск из корня проекта (при активированном виртуальном окружении):
    python -m app.seed
"""
from . import models, security
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

# role -> element -> permissions
RULES_MATRIX = {
    "admin": {
        "users": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "products": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "stores": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "orders": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        "access_rules": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
    },
    "manager": {
        "users": dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "products": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=False, delete_all=False),
        "stores": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=False, delete_all=False),
        "orders": dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=False),
        "access_rules": dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    "user": {
        "users": dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "products": dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "stores": dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "orders": dict(read=True, read_all=False, create=True, update=True, update_all=False, delete=True, delete_all=False),
        "access_rules": dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    "guest": {
        "users": dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "products": dict(read=False, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "stores": dict(read=False, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "orders": dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        "access_rules": dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
}

ELEMENTS = {
    "users": "Пользователи системы",
    "products": "Товары",
    "stores": "Магазины",
    "orders": "Заказы",
    "access_rules": "Правила доступа",
}

DEMO_USERS = [
    dict(email="admin@example.com", password="admin12345", last_name="Админов", first_name="Админ", role="admin"),
    dict(email="manager@example.com", password="manager12345", last_name="Менеджеров", first_name="Максим", role="manager"),
    dict(email="user@example.com", password="user12345", last_name="Юзеров", first_name="Юрий", role="user"),
    dict(email="guest@example.com", password="guest12345", last_name="Гостев", first_name="Глеб", role="guest"),
]


def seed():
    db = SessionLocal()
    try:

        roles = {}
        for name in RULES_MATRIX.keys():
            role = db.query(models.Role).filter(models.Role.name == name).first()
            if not role:
                role = models.Role(name=name)
                db.add(role)
                db.flush()
            roles[name] = role


        elements = {}
        for name, description in ELEMENTS.items():
            element = db.query(models.BusinessElement).filter(models.BusinessElement.name == name).first()
            if not element:
                element = models.BusinessElement(name=name, description=description)
                db.add(element)
                db.flush()
            elements[name] = element

        db.commit()


        for role_name, elements_perms in RULES_MATRIX.items():
            role = roles[role_name]
            for element_name, perms in elements_perms.items():
                element = elements[element_name]
                rule = (
                    db.query(models.AccessRule)
                    .filter(models.AccessRule.role_id == role.id, models.AccessRule.element_id == element.id)
                    .first()
                )
                if not rule:
                    rule = models.AccessRule(role_id=role.id, element_id=element.id)
                    db.add(rule)
                rule.read_permission = perms["read"]
                rule.read_all_permission = perms["read_all"]
                rule.create_permission = perms["create"]
                rule.update_permission = perms["update"]
                rule.update_all_permission = perms["update_all"]
                rule.delete_permission = perms["delete"]
                rule.delete_all_permission = perms["delete_all"]
        db.commit()


        for data in DEMO_USERS:
            if not db.query(models.User).filter(models.User.email == data["email"]).first():
                db.add(
                    models.User(
                        email=data["email"],
                        password_hash=security.hash_password(data["password"]),
                        last_name=data["last_name"],
                        first_name=data["first_name"],
                        role_id=roles[data["role"]].id,
                        is_active=True,
                    )
                )
        db.commit()

        print("База данных успешно наполнена тестовыми данными.")
        print("Демо-пользователи (email / пароль / роль):")
        for d in DEMO_USERS:
            print(f"  {d['email']} / {d['password']} / {d['role']}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
