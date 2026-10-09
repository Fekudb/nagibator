# Нагибатор диванных критиков: детектор токсичных комментариев (ML-бэкенд)

Бэкенд-сервис для классификации русскоязычных комментариев на токсичные и нейтральные.
Используется предобученная модель cointegrated/rubert-tiny-toxicity (RuBERT), которая понимает контекст и смысл фразы целиком.

## Установка

```bash
cd ml_api
python3 -m venv .venv
source .venv/bin/activate
make install
```

При первом запуске модель автоматически скачивается с HuggingFace (~50 МБ).

## Запуск сервера

```bash
make run
```

Swagger-документация доступна по адресу: http://localhost:8000/docs

## Запуск через Docker

```bash
make docker-build
make docker-run
```

Или из корневой папки:

```bash
docker compose up backend
```

## API

Полная спецификация контрактов — в файле [`docs/openapi.yaml`](docs/openapi.yaml).

- `POST /predict` — классификация текста. Тело запроса: `{"text": "ваш текст"}`. Ответ: `{"label": "toxic"|"neutral", "score": 0.93}`.
- `GET /stats` — общая статистика проверок (количество, процент токсичных, последние проверки).
- `GET /health` — проверка состояния сервиса. Ответ: `{"status": "ok"}`.

## Тестирование

```bash
make test
```

Тесты используют мок предиктора (модель не загружается) и временную SQLite-базу.

## Линтер

```bash
make lint          # проверка
make lint-fix      # автоисправление
```

## Makefile

| Команда            | Действие                                      |
|--------------------|-----------------------------------------------|
| `make run`         | Запуск uvicorn с --reload                     |
| `make install`     | Установка зависимостей                        |
| `make lint`        | Проверка кода (ruff)                          |
| `make lint-fix`    | Автоисправление (ruff)                        |
| `make test`        | Запуск тестов (pytest)                        |
| `make docker-build`| Сборка Docker-образа                          |
| `make docker-run`  | Запуск контейнера                             |
| `make clean`       | Удаление кэшей (__pycache__, .pyc и т.д.)     |

## Структура проекта

```
ml_api/
├── Makefile                 — команды сборки и запуска
├── api/
│   └── main.py              — FastAPI-приложение
├── domain/
│   └── entities.py           — модели данных (запрос, ответ, статистика)
├── ml/
│   └── predictor.py          — загрузка RuBERT и предсказание
├── db/
│   └── database.py           — работа с SQLite (сохранение результатов, статистика)
├── docs/
│   └── openapi.yaml          — OpenAPI-спецификация контрактов API
├── tests/
│   └── test_api.py           — тесты API (6 тестов)
├── Dockerfile
├── pyproject.toml        — конфигурация линтера (ruff)
└── requirements.txt
```
