#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Collecting static files details..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate

echo "Seeding initial data..."
python manage.py seed_data

echo "Starting application..."
exec "$@"
