import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # токен живёт 24 часа

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
