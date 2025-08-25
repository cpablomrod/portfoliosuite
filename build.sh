#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser if needed (run twice to ensure it works)
echo "Creating/updating admin superuser..."
python manage.py create_production_superuser --username=admin --email=admin@portfoliosuite.com || echo "First attempt failed, trying again..."
python manage.py create_production_superuser --username=admin --email=admin@portfoliosuite.com || echo "Admin creation completed"
