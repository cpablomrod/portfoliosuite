#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser if needed (optional - you can do this manually later)
# python manage.py shell -c "
# from django.contrib.auth.models import User
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@portfoliosuite.com', 'your-secure-password')
#     print('Superuser created')
# else:
#     print('Superuser already exists')
# "
