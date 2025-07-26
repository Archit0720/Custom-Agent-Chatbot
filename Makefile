.PHONY: help install run test lint format clean docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run the Streamlit application"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  clean       - Clean up temporary files"
	@echo "  docker-build- Build Docker image"
	@echo "  docker-run  - Run Docker container"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	streamlit run main.py

test:
	pytest tests/ -v

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black .
	isort .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

docker-build:
	docker build -t ai-character-chat .

docker-run:
	docker run -p 8501:8501 -e GROQ_API_KEY=$(GROQ_API_KEY) ai-character-chat

docker-compose-up:
	docker-compose up --build

docker-compose-down:
	docker-compose down

# Development helpers
dev-setup: install-dev
	pre-commit install

check: lint test

all: clean format lint test
