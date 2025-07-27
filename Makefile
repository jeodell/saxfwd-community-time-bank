# Django Timebank Makefile
# Common commands for development, translation, and deployment

.PHONY: help install dev up migrate makemigrations shell superuser test coverage clean collectstatic translations makemessages compilemessages build deploy

# Default target
help:
	@echo "Django Timebank - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install Python dependencies"
	@echo "  dev         - Install dependencies and setup development environment"
	@echo "  up          - Start development server"
	@echo "  shell       - Open Django shell"
	@echo "  superuser   - Create Django superuser"
	@echo ""
	@echo "Database:"
	@echo "  migrate     - Run database migrations"
	@echo "  makemigrations - Create new migrations"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run tests"
	@echo "  coverage    - Run tests with coverage report"
	@echo ""
	@echo "Static Files:"
	@echo "  collectstatic - Collect static files"
	@echo "  tailwind     - Build Tailwind CSS"
	@echo ""
	@echo "Translations:"
	@echo "  translations    - Generate and compile all translations"
	@echo "  makemessages    - Generate translation files"
	@echo "  compilemessages - Compile translation files"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build       - Full build process (like build.sh)"
	@echo "  deploy      - Build and prepare for deployment"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       - Clean up temporary files"
	@echo "  reset       - Reset database and migrations"

# Development setup
install:
	pip install -r requirements.txt

dev: install
	cd theme/static_src && npm install && cd ../..
	python manage.py tailwind build
	@echo "Development environment setup complete!"

up:
	python manage.py runserver

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

# Database commands
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

# Testing
test:
	python manage.py test

coverage:
	coverage run --source='.' manage.py test
	coverage report
	coverage html

# Static files
collectstatic:
	python manage.py collectstatic --noinput

tailwind:
	python manage.py tailwind build

# Translations
translations: makemessages compilemessages

makemessages:
	python manage.py makemessages -a --ignore=venv/* --ignore=staticfiles/* --ignore=static/*

compilemessages:
	python manage.py compilemessages

# Build and deployment
build:
	set -o errexit
	pip install -r requirements.txt
	cd theme/static_src && npm install && npm run build && cd ../..
	python manage.py tailwind build
	python manage.py collectstatic_s3
	python manage.py migrate
	python manage.py makemessages -a --ignore=venv/* --ignore=staticfiles/* --ignore=static/*
	python manage.py compilemessages

deploy: build
	@echo "Build complete! Ready for deployment."

# Maintenance
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/
	rm -rf staticfiles/
	@echo "Cleanup complete!"

reset:
	rm -f db.sqlite3
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	python manage.py makemigrations
	python manage.py migrate
	@echo "Database reset complete!"

# Quick development helpers
quick-dev: install migrate up

quick-test: test coverage

quick-translate: makemessages
	@echo "Translation files generated. Edit locale/*/LC_MESSAGES/django.po files, then run 'make compilemessages'"

# Environment-specific commands
local:
	export ENVIRONMENT=local && python manage.py runserver

prod-check:
	python manage.py check --deploy

# Backup and restore (if using SQLite)
backup:
	cp db.sqlite3 db.sqlite3.backup.$$(date +%Y%m%d_%H%M%S)

restore:
	@echo "Available backups:"
	@ls -la db.sqlite3.backup.* 2>/dev/null || echo "No backups found"
	@echo "To restore: cp db.sqlite3.backup.YYYYMMDD_HHMMSS db.sqlite3"