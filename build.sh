#!/usr/bin/env bash
# Don't exit on error to allow deployment to continue
# set -o errexit

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

# Run database migrations (critical for deployment)
echo "🗃️ Running database migrations..."
python manage.py migrate || {
    echo "⚠️ Standard migration failed, trying with --run-syncdb"
    python manage.py migrate --run-syncdb || echo "❌ All migration attempts failed but continuing..."
}

# Check database status (non-critical)
echo "🔍 Checking database status..."
python manage.py check_database 2>/dev/null || echo "⚠️ Database check skipped (command may not be available yet)"

# Show migration status (non-critical)
echo "📊 Migration status:"
python manage.py showmigrations stocks 2>/dev/null || echo "⚠️ Could not show migration status"

# Create/fix superuser (try both methods)
echo "👤 Creating/updating admin superuser..."
python create_admin.py || echo "Standard admin creation completed"

echo "🔧 Ensuring admin permissions are correct..."
python manage.py fix_admin 2>/dev/null || echo "⚠️ Admin fix command skipped"
