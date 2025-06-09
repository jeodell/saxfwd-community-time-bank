# Saxapahaw Timebank

A Django-based Saxapahaw Timebank application where members can offer services, track hours spent and received, and
manage their time bank accounts.

## Features

- User registration and authentication
- Service listing and management
- Service request and fulfillment system
- Time bank ledger for tracking hours
- User account page with history and settings

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up the database:

```bash
python manage.py migrate
```

4. Create a superuser:

```bash
python manage.py createsuperuser
```

5. Run the development server:

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

## Tailwind CSS

```bash
python manage.py tailwind build
python manage.py collectstatic --noinput
```

## Render Deployment

See [render.yaml](render.yaml) for the Render deployment configuration.
