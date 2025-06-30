set -o errexit
pip install -r requirements.txt
cd theme/static_src && npm install && npm run build && cd ../..
python manage.py tailwind build
python manage.py collectstatic_s3 --noinput
python manage.py migrate