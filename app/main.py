from fastapi import FastAPI

from .database import Base, engine
from .routers import admin, auth, business

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Custom Auth & RBAC API",
    description=(
        "Тестовое задание: собственная система аутентификации и авторизации "
        "(без использования готовой auth-системы фреймворка)."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(business.router)


@app.get("/", tags=["Служебное"])
def root():
    return {"detail": "API запущено. Интерактивная документация: /docs"}
