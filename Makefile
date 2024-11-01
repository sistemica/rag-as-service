.PHONY: help build run test clean lint format dev prod push logs backup venv venv-create venv-remove update-packages

# Variables
DOCKER_REGISTRY := ghcr.io
DOCKER_REPO := sistemica/rag-as-service
VERSION := $(shell git describe --tags --always --dirty)
CURRENT_DATE := $(shell date +%Y%m%d)
VENV_NAME := venv
PYTHON := python3.11
SHELL := /bin/bash

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image
	docker build -t $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(VERSION) .
	docker tag $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(VERSION) $(DOCKER_REGISTRY)/$(DOCKER_REPO):latest

dev: ## Start development environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod: ## Start production environment
	docker-compose up -d --build

push: ## Push the Docker image to registry
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(VERSION)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):latest

venv-create: ## Create virtual environment
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV_NAME)
	@echo "Virtual environment created. Activate it with: source $(VENV_NAME)/bin/activate"

venv-remove: ## Remove virtual environment
	@echo "Removing virtual environment..."
	@rm -rf $(VENV_NAME)

venv: ## Create and activate virtual environment, install dependencies
	@if [ ! -d "$(VENV_NAME)" ]; then \
		make venv-create; \
	fi
	@echo "Installing dependencies..."
	@source $(VENV_NAME)/bin/activate && pip install --upgrade pip
	@source $(VENV_NAME)/bin/activate && pip install -r requirements.txt

update-packages: ## Update all packages to their latest versions
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Virtual environment not found. Creating one..."; \
		make venv-create; \
	fi
	@echo "Updating all packages..."
	@source $(VENV_NAME)/bin/activate && \
	pip install --upgrade pip && \
	pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
	@echo "Freezing requirements..."
	@source $(VENV_NAME)/bin/activate && pip freeze > requirements.txt
	@echo "Requirements updated successfully!"

test: ## Run tests
	docker-compose run --rm app pytest

test-watch: ## Run tests in watch mode
	docker-compose run --rm app ptw

coverage: ## Run tests with coverage
	docker-compose run --rm app pytest --cov=app --cov-report=html

test-local: ## Run tests locally in virtual environment
	@source $(VENV_NAME)/bin/activate && pytest

lint: ## Run linters
	docker-compose run --rm app black .
	docker-compose run --rm app isort .
	docker-compose run --rm app flake8 .

lint-local: ## Run linters locally in virtual environment
	@source $(VENV_NAME)/bin/activate && black .
	@source $(VENV_NAME)/bin/activate && isort .
	@source $(VENV_NAME)/bin/activate && flake8 .

format: ## Format code
	docker-compose run --rm app black .
	docker-compose run --rm app isort .

format-local: ## Format code locally in virtual environment
	@source $(VENV_NAME)/bin/activate && black .
	@source $(VENV_NAME)/bin/activate && isort .

clean: ## Clean up Docker resources and virtual environment
	docker-compose down -v
	make venv-remove

logs: ## View logs
	docker-compose logs -f

backup: ## Backup database
	docker-compose exec db pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > backup_$(CURRENT_DATE).sql

restore: ## Restore database from backup
	docker-compose exec -T db psql -U $(POSTGRES_USER) $(POSTGRES_DB) < $(BACKUP_FILE)

shell: ## Open a shell in the app container
	docker-compose run --rm app /bin/bash

db-shell: ## Open a psql shell
	docker-compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

setup: venv ## Initial setup for development
	cp .env.example .env
	mkdir -p logs

health-check: ## Check service health
	curl -f http://localhost:8000/health

version: ## Show current version
	@echo $(VERSION)