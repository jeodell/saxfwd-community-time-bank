set -o errexit
pip install -r requirements.txt
cd theme/static_src && npm install && npm run build && cd ../..
python manage.py tailwind build
python manage.py collectstatic_s3
python manage.py migrate
DJANGO_SUPERUSER_PASSWORD=superuser python manage.py createsuperuser --noinput --email superuser@example.com
