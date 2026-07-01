from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Role(Base):
    """Роль пользователя: admin, manager, user, guest."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")
    access_rules = relationship("AccessRule", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    # Мягкое удаление: аккаунт остаётся в БД, но залогиниться нельзя
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")


class BusinessElement(Base):
    """Объект приложения, к которому применяются правила доступа
    (users, products, stores, orders, access_rules)."""

    __tablename__ = "business_elements"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    access_rules = relationship("AccessRule", back_populates="element")


class AccessRule(Base):
    """Правило: что роль может делать с элементом приложения.

    *_permission        — действие над СВОИМИ объектами (owner_id == user.id)
    *_all_permission     — действие над ВСЕМИ объектами, независимо от владельца
    create_permission не имеет "all"-варианта — создание не привязано к владельцу.
    """

    __tablename__ = "access_rules"

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    element_id = Column(Integer, ForeignKey("business_elements.id"), nullable=False)

    read_permission = Column(Boolean, default=False, nullable=False)
    read_all_permission = Column(Boolean, default=False, nullable=False)
    create_permission = Column(Boolean, default=False, nullable=False)
    update_permission = Column(Boolean, default=False, nullable=False)
    update_all_permission = Column(Boolean, default=False, nullable=False)
    delete_permission = Column(Boolean, default=False, nullable=False)
    delete_all_permission = Column(Boolean, default=False, nullable=False)

    role = relationship("Role", back_populates="access_rules")
    element = relationship("BusinessElement", back_populates="access_rules")

    __table_args__ = (UniqueConstraint("role_id", "element_id", name="uq_role_element"),)


class RevokedToken(Base):
    """Список отозванных (после logout / удаления аккаунта) JWT-токенов по их jti."""

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow)
