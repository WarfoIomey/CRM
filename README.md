# Mini-CRM System

Многопользовательская мини-CRM система с поддержкой нескольких организаций (multi-tenant)

## Стек технологий

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1C1C1C?style=for-the-badge&logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-92000?style=for-the-badge&logo=python&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## Возможности

- **Multi-tenant архитектура** - поддержка нескольких организаций
- **Ролевая модель** - owner, admin, manager, member
- **Управление контактами** - клиенты и потенциальные партнеры
- **Воронка продаж** - сделки со стадиями и статусами
- **Задачи** - управление задачами по сделкам
- **Таймлайн активности** - история действий по сделкам
- **Аналитика** - сводки и воронка продаж
- **JWT аутентификация** - access/refresh токены

## Структура проекта
```
mini-crm/
├── src/
│ ├── api/ # Эндпоинты и роутеры
│ │ ├── v1/ # API v1
│ │ │ ├── auth.py
│ │ │ ├── organizations.py
│ │ │ ├── contacts.py
│ │ │ ├── deals.py
│ │ │ ├── tasks.py
│ │ │ ├── activities.py
│ │ │ └── analytics.py
│ │ └── dependencies.py # Зависимости и middleware
│ ├── core/ # Ядро приложения
│ │ ├── config.py # Конфигурация
│ │ ├── security.py # JWT и хеширование
│ │ └── database.py # Настройки БД
│ ├── models/ # SQLAlchemy модели
│ │ ├── user.py
│ │ ├── organization.py
│ │ ├── contact.py
│ │ ├── deal.py
│ │ ├── task.py
│ │ └── activity.py
│ ├── schemas/ # Pydantic схемы
│ │ ├── auth.py
│ │ ├── user.py
│ │ ├── organization.py
│ │ ├── contact.py
│ │ ├── deal.py
│ │ ├── task.py
│ │ ├── activity.py
│ │ └── analytics.py
│ ├── services/ # Бизнес-логика
│ │ ├── auth_service.py
│ │ ├── organization_service.py
│ │ ├── contact_service.py
│ │ ├── deal_service.py
│ │ ├── task_service.py
│ │ └── analytics_service.py
│ ├── repositories/ # Работа с данными
│ │ ├── base.py
│ │ ├── user_repository.py
│ │ ├── organization_repository.py
│ │ ├── contact_repository.py
│ │ ├── deal_repository.py
│ │ ├── task_repository.py
│ │ └── activity_repository.py
│ ├── migrations/ # Alembic миграции
│ └── main.py # Точка входа
├── tests/
│ ├── unit/ # Юнит-тесты
│ ├── integration/ # Интеграционные тесты
│ ├── conftest.py # Фикстуры
│ └── test_data/ # Тестовые данные
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## Настройка окружения

1. Скопируйте `.env.example` в `.env` и заполните значениями:

```ini
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mini_crm
DB_USER=your_db_user
DB_PASS=your_db_password

# Security
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```
2. Скопируйте `.test.env.example` в `.test.env` и заполните значениями:

```ini
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=spimex_db_test
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
MODE=TEST
```
## 🏃 Запуск проекта

Требования:
- Python 3.10+
- Docker
- PostgreSQL

```bash
    docker compose up --build
    docker compose exec backend alembic upgrade head
```

После успешного выполнения этих команд приложение будет доступно по адресу <http://localhost:8000/docs>.

## 📚 API Документация

После запуска доступны:
 - Swagger UI: http://localhost:8000/docs
 - ReDoc: http://localhost:8000/redoc

## Аутентификация

### Регистрация
```
POST /api/v1/auth/register
{
  "email": "owner@example.com",
  "password": "StrongPassword123",
  "name": "Alice Owner",
  "organization_name": "Acme Inc"
}
```

### Логин
```
POST /api/v1/auth/login
{
  "email": "owner@example.com",
  "password": "StrongPassword123"
}
```

### Заголовки для следующих запросов
```
Authorization: Bearer <access_token>
X-Organization-Id: <organization_id>
```

## Тестирование

```bash
# Запуск тестов
pytest
```

## Ролевая модель
```
Owner - Полный доступ ко всем функциям организации
Admin - Почти полный доступ, кроме удаления организации
Manager - Управление всеми сущностями, кроме настроек организации
Member - Только свои контакты, сделки и задачи
```

## Бизнес-правила
```
Нельзя закрыть сделку со статусом won если amount <= 0
Нельзя удалить контакт с активными сделками
Нельзя создать задачу для чужой сделки (для роли member)
Задачи не могут иметь дату выполнения в прошлом
Ограничения на переход стадий сделок
```

## Модель данных
```
Система включает следующие основные сущности:
Organization - Организации
User - Пользователи
OrganizationMember - Участники организаций
Contact - Контакты
Deal - Сделки
Task - Задачи
Activity - Активности
```