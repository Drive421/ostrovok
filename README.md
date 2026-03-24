# Test task: Blog API (FastAPI + PostgreSQL + Redis)

Привет. Это тестовое задание на Junior ETL Developer.  
Я сделал API для постов + кеш популярных (точечно по `id`) через Redis.

## Что тут реализовано

- CRUD для постов:
  - `POST /posts`
  - `GET /posts/{id}`
  - `PATCH /posts/{id}` (частичное обновление)
  - `DELETE /posts/{id}`
- Кеширование `GET /posts/{id}`:
  - сначала проверка Redis по ключу `post:{id}`
  - если в Redis нет -> чтение из PostgreSQL -> запись в Redis
- Инвалидация кеша:
  - после `PATCH /posts/{id}` удаляется `post:{id}`
  - после `DELETE /posts/{id}` удаляется `post:{id}`
- Интеграционные тесты кеширования (`pytest`)

## Стек

- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy (async) + Alembic
- pytest + pytest-asyncio + httpx
- Docker Compose

## Архитектура (коротко)

1. FastAPI принимает запрос от клиента.
2. Роут передает работу в `PostsService`.
3. Дальше логика зависит от типа запроса:
   - `GET /posts/{id}`:
     - сначала проверяем Redis по ключу `post:{id}`;
     - если нашли — сразу возвращаем;
     - если не нашли — читаем из PostgreSQL, кладем в Redis, возвращаем.
   - `PATCH /posts/{id}`:
     - обновляем пост в PostgreSQL;
     - удаляем ключ `post:{id}` в Redis (инвалидация).
   - `DELETE /posts/{id}`:
     - удаляем пост из PostgreSQL;
     - удаляем ключ `post:{id}` в Redis.

То есть PostgreSQL — основной источник данных, Redis — только ускоритель чтения.

## Почему такой подход к кешированию

Выбран `cache-aside`, потому что для этой задачи это самый простой и надежный вариант:

- Легко понять и поддерживать.
- Нет сложной синхронизации между БД и кешем.
- Чтение ускоряется на повторных запросах.
- Консистентность контролируется просто: на `PATCH/DELETE` делаем `DEL` ключа.

Для тестового это лучший баланс между простотой и рабочим результатом.

## Структура проекта (главное)

- `app/main.py` — вход в приложение
- `app/routers/posts.py` — HTTP-ручки
- `app/services/posts_service.py` — бизнес-логика CRUD + кеш
- `app/services/redis_cache.py` — обертка над Redis
- `app/schemas/posts.py` — Pydantic-схемы
- `database/models.py` — ORM-модель `Post`
- `database/session.py` — async-сессия SQLAlchemy
- `alembic/` — миграции
- `tests/` — интеграционные тесты
- `.env` — переменные окружения
- `docker-compose.yml` — Postgres + Redis

## Переменные окружения (`.env`)

Важно: так как API запускается локально из `.venv`, здесь используются **внешние (host) порты** из `docker-compose`.

Примечание: `.env` в этом тестовом репозитории оставлен специально, чтобы проект можно было сразу запустить без лишней возни. В нем нет секретных продовых данных, только локальные тестовые значения.

## Как запустить

### 0) Скачать репозиторий

```powershell
git clone https://github.com/Drive421/ostrovok.git
```

### Важно про Docker

В текущем варианте PostgreSQL и Redis поднимаются через `docker compose`, поэтому без Docker Desktop (или другого Docker Engine) этот способ запуска не сработает.

### 1) Поднять БД и Redis

```powershell
docker compose up -d
docker compose ps
```

### 2) Создать и активировать виртуальное окружение

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Применить миграции

```powershell
alembic upgrade head
```

### 4) Запустить API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Проверка:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## Как запустить тесты

```powershell
pytest -q
```

Ожидаемо:
- 3 интеграционных теста проходят
- проверяется заполнение кеша и инвалидация на `PATCH/DELETE`

## Что можно улучшить дальше (если было бы время)

- добавить list-ручку (`GET /posts`) с пагинацией;
- реализовать безопасную систему аутентификации и авторизации с использованием кастомных Depends для гибкого управления доступом и разграничения прав пользователей;
- добавить CI (например GitHub Actions), чтобы тесты гонялись автоматически.
