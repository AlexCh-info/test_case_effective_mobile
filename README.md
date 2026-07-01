# Custom Auth & RBAC API

Тестовое задание: backend-приложение с собственной системой аутентификации
и авторизации, реализованной с нуля (без `django.contrib.auth`, без готовых
permission-классов DRF и т.п.).

Стек: **FastAPI + SQLAlchemy + SQLite + JWT (PyJWT) + bcrypt**.

FastAPI выбран вместо Django/DRF, потому что вся логика прав доступа в этом
задании всё равно пишется вручную — фреймворк здесь используется только как
маршрутизатор и валидатор данных, а не как готовая auth-система. Это меньше
"магии" и проще для запуска в PyCharm без предварительного знания Django.

---

## 1. Аутентификация — как это работает

- Пароли хранятся **не в открытом виде**, а как bcrypt-хэш (`bcrypt.hashpw`).
- При логине (`POST /auth/login`) выдаётся **JWT-токен** (`PyJWT`), в него
  зашиты `sub` (id пользователя), `jti` (уникальный id самого токена) и время
  жизни (24 часа).
- Клиент передаёт токен в заголовке `Authorization: Bearer <token>` в каждом
  запросе. Никакого `django.contrib.auth` / `Session` middleware — пользователь
  определяется вручную в `app/dependencies.py::get_current_user`.
- **Logout не тривиален для JWT** (токен нельзя "отозвать" сам по себе), поэтому
  реализована таблица `revoked_tokens`: при logout `jti` токена записывается
  туда, и `get_current_user` при каждом запросе проверяет, не отозван ли токен.
- **Удаление аккаунта — мягкое**: `is_active` пользователя становится `False`,
  текущий токен отзывается, но запись в БД остаётся. Логин с этим email
  становится невозможным.
- Если пользователя не удалось определить по токену → **401**.
  Если пользователь определён, но прав на ресурс нет → **403**.

## 2. Схема авторизации (RBAC)

Права строятся на трёх таблицах, как и предлагалось в задании:

### `roles` — роли пользователей
`admin`, `manager`, `user`, `guest`.

### `business_elements` — объекты приложения, к которым применяются права
| name | описание |
|---|---|
| `users` | Пользователи системы |
| `products` | Товары (mock) |
| `stores` | Магазины (mock) |
| `orders` | Заказы (mock) |
| `access_rules` | Сами правила доступа |

### `access_rules` — правило "роль ↔ элемент"
| Столбец | Тип | Смысл |
|---|---|---|
| `role_id` | FK | какая роль |
| `element_id` | FK | к какому элементу |
| `read_permission` | bool | читать **свои** объекты (где `owner_id == user.id`) |
| `read_all_permission` | bool | читать **все** объекты, независимо от владельца |
| `create_permission` | bool | создавать объекты (владельцем становится текущий пользователь) |
| `update_permission` / `update_all_permission` | bool | изменять свои / любые |
| `delete_permission` / `delete_all_permission` | bool | удалять свои / любые |

**Логика проверки** (см. `app/routers/business.py::_check_object_access`):
1. Если у роли есть `*_all_permission` для элемента — доступ разрешён к любому объекту.
2. Иначе, если есть `*_permission` **и** `object.owner_id == current_user.id` — разрешено.
3. Иначе — `403 Forbidden`.
4. Если ни `*_permission`, ни `*_all_permission` вообще не выставлены — тоже `403`.

Для списков (`GET /business/products` и т.п.) применяется то же правило:
`read_all` → отдаём весь список, только `read` → фильтруем по `owner_id`, иначе — `403`.

### Тестовые данные (наполняются скриптом `app/seed.py`)

| Роль | users | products | stores | orders | access_rules |
|---|---|---|---|---|---|
| **admin** | всё | всё | всё | всё | всё |
| **manager** | read_all | read_all + create/update (не свои тоже) | read_all + create/update | read_all + create/update/delete | read_all |
| **user** | только себя | read_all (каталог), без изменений | read_all (каталог) | только свои: read/create/update/delete | нет доступа |
| **guest** | нет доступа | read_all (публичный каталог) | read_all | нет доступа | нет доступа |

Полную матрицу правил можно посмотреть в `app/seed.py` (`RULES_MATRIX`) —
их же увидит и сможет отредактировать администратор через `/admin/access-rules`.

## 3. Демо-пользователи

После `python -m app.seed`:

| email | пароль | роль |
|---|---|---|
| admin@example.com | admin12345 | admin |
| manager@example.com | manager12345 | manager |
| user@example.com | user12345 | user |
| guest@example.com | guest12345 | guest |

## 4. Mock-объекты бизнес-приложения

По условию задания таблицы для товаров/магазинов/заказов создавать не нужно —
они реализованы как списки в памяти (`app/routers/business.py`), к которым
применяются те же правила из `access_rules`. Это позволяет продемонстрировать
работу системы прав без раздувания схемы БД.

---

## 5. Структура проекта

```
auth_rbac_api/
├── app/
│   ├── main.py            # сборка FastAPI-приложения, подключение роутеров
│   ├── config.py           # SECRET_KEY, DATABASE_URL и т.п. (из .env)
│   ├── database.py         # SQLAlchemy engine / session
│   ├── models.py            # таблицы: User, Role, BusinessElement, AccessRule, RevokedToken
│   ├── schemas.py           # pydantic-схемы запросов/ответов
│   ├── security.py          # bcrypt-хэширование, создание/проверка JWT
│   ├── dependencies.py     # get_current_user, require_admin, get_rule
│   ├── seed.py               # наполнение БД ролями/правилами/демо-юзерами
│   └── routers/
│       ├── auth.py          # register / login / logout / me
│       ├── admin.py         # CRUD ролей, элементов, правил доступа (только admin)
│       └── business.py      # mock-объекты: products, stores, orders, users
├── run.py                   # точка входа для запуска из PyCharm
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 6. Запуск в PyCharm с нуля

1. **Открыть проект**: `File → Open...` → выбрать папку `auth_rbac_api`.
2. **Создать виртуальное окружение**, если PyCharm не предложил сам:
   `File → Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Virtualenv`,
   Python 3.10+.
3. **Установить зависимости** — открыть встроенный терминал PyCharm (`Alt+F12`) и выполнить:
   ```bash
   pip install -r requirements.txt
   ```
4. **Создать файл `.env`** в корне проекта (скопировать `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Значения по умолчанию подходят для локального запуска, можно ничего не менять.
5. **Наполнить базу тестовыми данными**:
   ```bash
   python -m app.seed
   ```
   Это создаст файл `app.db` (SQLite) в корне проекта.
6. **Запустить сервер** — открыть `run.py` и нажать зелёный ▶ (Run), либо в терминале:
   ```bash
   python run.py
   ```
7. Открыть в браузере **http://127.0.0.1:8000/docs** — интерактивная документация
   Swagger UI, через неё удобно всё тестировать (кнопка "Authorize" принимает
   заголовок `Bearer <token>`, который выдаёт `/auth/login`).

Пересоздать базу с нуля: удалить файл `app.db` и снова выполнить `python -m app.seed`.

---

## 7. Основные эндпоинты

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/auth/register` | все | регистрация (роль по умолчанию — `user`) |
| POST | `/auth/login` | все | вход, выдаёт JWT |
| POST | `/auth/logout` | авторизован | отзывает текущий токен |
| GET | `/auth/me` | авторизован | текущий профиль |
| PATCH | `/auth/me` | авторизован | редактирование профиля |
| DELETE | `/auth/me` | авторизован | мягкое удаление аккаунта |
| GET/POST | `/admin/roles` | только admin | список / создание ролей |
| GET/POST | `/admin/business-elements` | только admin | список / создание элементов |
| GET/POST | `/admin/access-rules` | только admin | просмотр / изменение правил доступа |
| DELETE | `/admin/access-rules/{id}` | только admin | удаление правила |
| GET/POST/DELETE | `/business/products` | по правилам RBAC | mock-товары |
| GET/POST/DELETE | `/business/stores` | по правилам RBAC | mock-магазины |
| GET/POST/DELETE | `/business/orders` | по правилам RBAC | mock-заказы |
| GET | `/business/users` | по правилам RBAC | список пользователей |

Быстрая проверка через `curl`:
```bash
# логин
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "user12345"}'

# запрос с токеном
curl http://127.0.0.1:8000/business/orders \
  -H "Authorization: Bearer <ВСТАВИТЬ_ТОКЕН>"
```

---

## 8. Публикация на GitHub

```bash
git init
git add .
git commit -m "Custom auth & RBAC API (тестовое задание)"
git branch -M main
git remote add origin https://github.com/<ваш-логин>/<название-репозитория>.git
git push -u origin main
```

Файл `.env` и `app.db` в репозиторий не попадут — они уже в `.gitignore`.
Проверяющий сможет развернуть проект с нуля по инструкции из раздела 6.
