.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linters
	flake8 app tests
	black --check app tests
	isort --check-only app tests
	mypy app --ignore-missing-imports

format: ## Format code
	black app tests
	isort app tests

clean: ## Clean cache and build files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create new migration (use name=your_migration_name)
	alembic revision --autogenerate -m "$(name)"

migrate-down: ## Rollback last migration
	alembic downgrade -1

seed: ## Seed database with initial data
	python scripts/seed_data.py

db-reset: ## Reset database (DANGER!)
	alembic downgrade base
	alembic upgrade head
	python scripts/seed_data.py

shell: ## Open Python shell with app context
	python -i -c "from app.database import get_db; from app.models import *; print('Database models loaded')"

redis-cli: ## Connect to Redis CLI
	redis-cli

psql: ## Connect to PostgreSQL
	psql $(DATABASE_URL)

backup-db: ## Backup database
	pg_dump $(DATABASE_URL) > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database from backup (use file=backup.sql)
	psql $(DATABASE_URL) < $(file)

security-scan: ## Run security scan
	bandit -r app -ll
	safety check

.DEFAULT_GOAL := help
