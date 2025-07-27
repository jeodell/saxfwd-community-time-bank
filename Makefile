# Django Timebank Makefile
# Common commands for development, translation, and deployment

.PHONY: help install dev up migrate makemigrations shell superuser collectstatic translations format

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
	@echo "  migrate        - Run database migrations"
	@echo "  makemigrations - Create new migrations"
	@echo ""
	@echo "Static Files:"
	@echo "  collectstatic - Collect static files"
	@echo "  tailwind      - Build Tailwind CSS"
	@echo "  format        - Format HTML templates with djhtml"
	@echo ""
	@echo "Translations:"
	@echo "  translations    - Generate and compile all translations"
	@echo ""

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

# Static files
collectstatic:
	python manage.py collectstatic --noinput

tailwind:
	python manage.py tailwind build

format:
	djhtml templates/

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
