#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser if needed
echo "Creating/updating admin superuser..."
python create_admin.py || echo "Admin creation completed with fallback"
