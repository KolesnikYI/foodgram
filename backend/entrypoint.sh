#!/bin/sh
set -e

echo "Apply migrations"
python manage.py migrate

echo "Import tags"
python manage.py import_tags

echo "Import ingridients"
python manage.py import_ingredients

echo "Create test users"
python manage.py loaddata ../data/users.json

echo "Create test recipes"
mkdir -p media/recipes/images
cp -n ../data/images/*.jpg media/recipes/images/
python manage.py loaddata ../data/recipes.json

echo "Create superuser"
python manage.py createsuperuser --noinput || echo "Superuser already exists"

echo "Collect static"
python manage.py collectstatic --noinput

echo "Copy static to volume"
mkdir -p /backend_static/
cp -r /app/backend/collected_static/. /backend_static/

echo "Start server"
exec "$@"
