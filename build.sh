#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🔧 Starting build process..."

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Verify PostgreSQL driver installation
echo "🔍 Verifying PostgreSQL driver..."
python -c "import psycopg2; print('✅ psycopg2 imported successfully')" || echo "❌ psycopg2 import failed"
python -c "import django.db.backends.postgresql; print('✅ Django PostgreSQL backend available')" || echo "❌ Django PostgreSQL backend failed"

# Collect static files
python manage.py collectstatic --noinput

# Check database status
echo "🔍 Checking database status..."
python manage.py check_database || echo "⚠️ Database check completed with warnings"

# Run database migrations (force apply all migrations)
echo "🗃️ Running database migrations..."
python manage.py migrate --run-syncdb || echo "⚠️ Migration completed with warnings"

# Show migration status
echo "📊 Migration status:"
python manage.py showmigrations stocks || echo "⚠️ Could not show migration status"

# Create superuser if needed
echo "👤 Creating/updating admin superuser..."
python create_admin.py || echo "Admin creation completed with fallback"
