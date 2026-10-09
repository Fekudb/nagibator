APP_NAME = ml_api
DOCKER_IMAGE = $(APP_NAME)
PORT = 8000

.PHONY: run install lint test docker-build docker-run clean

run:
	uvicorn api.main:app --host 0.0.0.0 --port $(PORT) --reload

install:
	pip install -r requirements.txt

lint:
	ruff check .

lint-fix:
	ruff check --fix .

test:
	pytest tests/

docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run:
	docker run --rm -p $(PORT):$(PORT) $(DOCKER_IMAGE)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
