[![Main Foodgram workflow](https://github.com/KolesnikYI/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/KolesnikYI/foodgram/actions/workflows/main.yml)

# Foodgram

Пример рабочего проекта, развернутого в ести можно посмотреть [здесь](https://kyi.ddns.net/).

## Описание проекта

Foodgram — это сервис для публикации рецептов.

Пользователи могут:

- создавать и редактировать свои рецепты;
- подписываться на других авторов;
- добавлять рецепты в избранное;
- формировать список покупок и скачивать его в агрегированном виде.

Проект состоит из backend (Django + DRF), frontend (React),
nginx и PostgreSQL, запускаемых в Docker-контейнерах.

Важно: в рамках учебного проекта автором реализована backend-часть и
инфраструктура. Frontend, исходная API-документация, тестовые
данные (`data/`) и Postman-коллекция предоставлены Яндекс Практикумом.

## Стек технологий

- Python 3.12
- Django
- Django REST Framework
- Djoser (token auth)
- PostgreSQL
- Gunicorn
- Nginx
- Docker / Docker Compose
- React

## Как развернуть проект в Docker

1. Склонируйте репозиторий:

   ```bash
   git clone git@github.com:KolesnikYI/foodgram.git
   cd foodgram
   ```

2. Создайте файл `.env` в корне проекта со следующими переменными:

   ```env
   SQLITE=False
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=foodgram_password
   POSTGRES_DB=foodgram
   DB_HOST=db
   DB_PORT=5432

   SECRET_KEY=<secret_key>
   DEBUG=False
   POSTMAN=True
   ALLOWED_HOSTS=<Your_dns>,<your_ip>
   ```

3. Запустите контейнеры:

   ```bash
   docker compose -f infra/docker-compose.yml up -d --build
   ```

4. При старте backend-контейнера скрипт `backend/entrypoint.sh`
   автоматически:

   - применяет миграции;
   - импортирует теги и ингредиенты;
   - загружает тестовых пользователей и рецепты из `data/`;
   - собирает статику.

5. Проект будет доступен по адресам:
   - frontend: `http://localhost:9000/`
   - API: `http://localhost:9000/api/`
   - документация API: `http://localhost:9000/api/docs/`
   - админка: `http://localhost:9000/admin/`

Остановить контейнеры:

```bash
docker compose -f infra/docker-compose.yml down
```

## Как наполнить БД данными

Наполнение выполняется автоматически через `entrypoint.sh`. Команды
можно запустить и вручную:

### Импорт ингредиентов

```bash
docker compose -f infra/docker-compose.yml exec backend \
  python manage.py import_ingredients
```

Опция `--path` — путь к своему JSON-файлу (по умолчанию
`data/ingredients.json`).

### Импорт базовых тегов

```bash
docker compose -f infra/docker-compose.yml exec backend \
  python manage.py import_tags
```

Команда создаёт теги, если их ещё нет.

### Тестовые пользователи и рецепты

```bash
docker compose -f infra/docker-compose.yml exec backend \
  python manage.py loaddata ../data/users.json ../data/recipes.json
```

## Как открыть документацию API
### При локальном развертывании

- Redoc: `http://localhost:9000/api/docs/`
- OpenAPI-схема: `docs/openapi-schema.yml`

### На уже развернутом в сети приложении

Посмотреть можно [здесь](https://kyi.ddns.net/api/docs/)



## Примеры запросов/ответов

### 1) Получить список рецептов

**Запрос**

```http
GET /api/recipes/?page=1&limit=6 HTTP/1.1
Host: localhost:9000
```

**Пример ответа (200 OK)**

```json
{
  "count": 123,
  "next": "http://localhost:9000/api/recipes/?page=2&limit=6",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Омлет",
      "text": "Взбить яйца и обжарить.",
      "cooking_time": 10,
      "is_favorited": false,
      "is_in_shopping_cart": false
    }
  ]
}
```

### 2) Получить токен авторизации

**Запрос**

```http
POST /api/auth/token/login/ HTTP/1.1
Host: localhost:9000
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strong-password"
}
```

**Пример ответа (200 OK)**

```json
{
  "auth_token": "<token_value>"
}
```

### 3) Добавить рецепт в избранное

**Запрос**

```http
POST /api/recipes/1/favorite/ HTTP/1.1
Host: localhost:9000
Authorization: Token <token_value>
```

**Пример ответа (201 Created)**

```json
{
  "id": 1,
  "name": "Омлет",
  "image": "http://localhost:9000/media/recipes/images/omlet.jpg",
  "cooking_time": 10
}
```

## Автор
Колесник Ян - студент Yandex practicum.
#### Контакты для связи:
- kolesnik-y-i@yandex.ru - почта
- [Профиль в GitHub](https://github.com/KolesnikYI)
- [Написать в телеграмм](https://t.me/YanKolesnik)

