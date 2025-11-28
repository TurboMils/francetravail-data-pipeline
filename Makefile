.PHONY: help venv install install-dev lint format test clean run-api run-streamlit run-consumer

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

lint:
	$(BIN)/ruff check src tests
	$(BIN)/black --check src tests
	$(BIN)/isort --check-only src tests

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
	PYTHONPATH=src $(BIN)/streamlit run streamlit_app/app.py

run-consumer:
	PYTHONPATH=src $(BIN)/python -m kafka_consumer.consumer
