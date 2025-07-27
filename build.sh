set -o errexit
pip install -r requirements.txt
cd theme/static_src && npm install && npm run build && cd ../..
python manage.py tailwind build
python manage.py collectstatic_s3
python manage.py migrate
python manage.py makemessages -a --ignore=venv/* --ignore=staticfiles/* --ignore=static/*
python manage.py compilemessages
