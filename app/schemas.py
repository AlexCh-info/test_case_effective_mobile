from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field



class UserRegister(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=6)
    password_confirm: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserOut(BaseModel):
    id: int
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"



class RoleOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str


class BusinessElementOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BusinessElementCreate(BaseModel):
    name: str
    description: Optional[str] = None


class AccessRuleOut(BaseModel):
    id: int
    role_id: int
    element_id: int
    read_permission: bool
    read_all_permission: bool
    create_permission: bool
    update_permission: bool
    update_all_permission: bool
    delete_permission: bool
    delete_all_permission: bool

    class Config:
        from_attributes = True


class AccessRuleUpsert(BaseModel):
    role_id: int
    element_id: int
    read_permission: bool = False
    read_all_permission: bool = False
    create_permission: bool = False
    update_permission: bool = False
    update_all_permission: bool = False
    delete_permission: bool = False
    delete_all_permission: bool = False
