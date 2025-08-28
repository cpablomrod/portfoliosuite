#!/usr/bin/env python
"""
Simple admin creation script using Django's built-in methods
"""
import os
import django
from django.core.management import execute_from_command_line

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings_render_free')
django.setup()

from django.contrib.auth.models import User

def create_simple_admin():
    try:
        # Simple approach - delete and recreate admin user
        username = 'admin'
        email = 'admin@portfoliosuite.com'
        password = 'SimpleAdmin2025!'
        
        # Delete existing admin user if exists
        User.objects.filter(username=username).delete()
        
        # Create new superuser
        User.objects.create_superuser(username, email, password)
        
        print(f"✅ Created admin user: {username}")
        print(f"✅ Password: {password}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = create_simple_admin()
    if success:
        print("\n🎉 Admin ready!")
        print("Username: admin")
        print("Password: SimpleAdmin2025!")
    else:
        print("\n❌ Failed to create admin")
