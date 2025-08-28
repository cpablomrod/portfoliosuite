#!/usr/bin/env python
"""
Diagnostic script to check Django admin console issues
This script will run basic health checks and attempt to create/verify admin user
"""
import os
import sys
import django

def main():
    print("🔍 Django Admin Diagnostic Script")
    print("=" * 50)
    
    try:
        # Set up Django environment
        if 'RENDER' in os.environ:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings_render_free')
        else:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings')
        
        django.setup()
        
        print("✅ Django setup successful")
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    # Test database connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check if admin user exists
    try:
        from django.contrib.auth.models import User
        admin_users = User.objects.filter(is_superuser=True)
        
        if admin_users.exists():
            print(f"✅ Found {admin_users.count()} admin user(s):")
            for user in admin_users:
                print(f"   - Username: {user.username}, Active: {user.is_active}, Staff: {user.is_staff}")
        else:
            print("⚠️  No admin users found")
            
    except Exception as e:
        print(f"❌ Error checking admin users: {e}")
        return False
    
    # Test admin site imports
    try:
        from django.contrib import admin
        from django.urls import reverse
        print("✅ Admin site imports successful")
    except Exception as e:
        print(f"❌ Admin site import failed: {e}")
        return False
    
    # Check admin URL configuration
    try:
        from django.urls import reverse
        admin_url = reverse('admin:index')
        print(f"✅ Admin URL pattern exists: {admin_url}")
    except Exception as e:
        print(f"❌ Admin URL configuration error: {e}")
        return False
    
    # Test SupportMessage model
    try:
        from stocks.models import SupportMessage
        count = SupportMessage.objects.count()
        print(f"✅ SupportMessage model working, {count} messages in database")
    except Exception as e:
        print(f"❌ SupportMessage model error: {e}")
        return False
    
    # Try to create/update admin user
    try:
        from django.contrib.auth.models import User
        from django.db import transaction
        
        username = 'admin'
        password = 'SimpleAdmin2025!'
        email = 'admin@portfoliosuite.com'
        
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True
                }
            )
            
            # Always update the password and permissions
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.save()
            
            if created:
                print(f"✅ Created admin user: {username}")
            else:
                print(f"✅ Updated admin user: {username}")
            
            print(f"🔑 Admin credentials:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Email: {email}")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    # Final verification
    try:
        test_user = User.objects.get(username='admin')
        print(f"✅ Admin user verification:")
        print(f"   ID: {test_user.id}")
        print(f"   Username: {test_user.username}")
        print(f"   Email: {test_user.email}")
        print(f"   Is Active: {test_user.is_active}")
        print(f"   Is Staff: {test_user.is_staff}")
        print(f"   Is Superuser: {test_user.is_superuser}")
        print(f"   Last Login: {test_user.last_login}")
        
    except Exception as e:
        print(f"❌ Admin user verification failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All checks passed! Admin should be working now.")
    print("📝 Try logging in at: /admin/")
    print(f"🔐 Username: admin")
    print(f"🔐 Password: SimpleAdmin2025!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
