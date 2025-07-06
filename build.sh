set -o errexit
pip install -r requirements.txt
cd theme/static_src && npm install && npm run build && cd ../..
python manage.py tailwind build
python manage.py collectstatic_s3
python manage.py migrate
python manage.py create_admin \
  --email admin@example.com \
  --password securepassword123 \
  --first-name Admin \
  --last-name User \
  --phone "555-1234" \
  --address "123 Main St" \
  --bio "System administrator"
