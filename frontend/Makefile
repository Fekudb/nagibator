APP_NAME = frontend
DOCKER_IMAGE = $(APP_NAME)
PORT = 5001

.PHONY: run install lint test docker-build docker-run clean

run:
	python3 run.py

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
