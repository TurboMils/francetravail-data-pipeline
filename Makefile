.PHONY: help venv install install-dev lint format test clean run-api run-streamlit run-consumer produce-offers docker-up kafka-create-topics generate-fernet-key airflow-up airflow-down

PYTHON := python3.12
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "Cibles disponibles :"
	@echo "  make venv          - Crée l'environnement virtuel"
	@echo "  make install       - Installe les dépendances (prod)"
	@echo "  make install-dev   - Installe les dépendances (prod + dev)"
	@echo "  make lint          - Lint (ruff, black --check, isort --check-only)"
	@echo "  make format        - Formatage (black, isort, ruff --fix)"
	@echo "  make test          - Lance pytest"
	@echo "  make run-api       - Lance l'API FastAPI (dev)"
	@echo "  make run-streamlit - Lance l'app Streamlit (dev)"
	@echo "  make run-consumer  - Lance le consumer Kafka (dev)"

venv:
	$(PYTHON) -m venv $(VENV)
	@echo "Environnement virtuel créé. Active : source $(VENV)/bin/activate"

install: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .
	@echo "Dépendances production installées"

install-dev: venv
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e '.[dev]'
	@echo "Dépendances production + dev installées"

lint: venv
	$(BIN)/ruff check src tests
	$(BIN)/black --check src tests
	$(BIN)/isort --check-only src tests

fix: venv
	$(BIN)/ruff check src tests --fix

type: venv
	$(BIN)/mypy src

format:
	$(BIN)/black src tests
	$(BIN)/isort src tests
	$(BIN)/ruff check --fix src tests

test:
	$(BIN)/pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov
	@echo "Nettoyage terminé"

run-api:
	PYTHONPATH=src $(BIN)/uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-streamlit:
	PYTHONPATH=src $(BIN)/streamlit run src/streamlit_app/app.py

run-consumer:
	KAFKA_BOOTSTRAP_SERVERS=localhost:9092 PYTHONPATH=src $(BIN)/python -m kafka_consumer.consumer

produce-offers: 
	PYTHONPATH=src $(BIN)/python scripts/produce_offers.py --count 100

docker-build:
	cd docker && docker-compose up -d

kafka-create-topics: 
	bash ./scripts/create_kafka_topics.sh

generate-fernet-key: 
	@$(BIN)/python scripts/generate_fernet_key.py

airflow-up: 
	cd docker && docker-compose up -d airflow-webserver airflow-scheduler

airflow-down:
	cd docker && docker-compose stop airflow-webserver airflow-scheduler
