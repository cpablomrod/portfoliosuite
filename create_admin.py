#!/usr/bin/env python
"""
One-time script to create admin user for production
Run this with: python create_admin.py
"""
import os
import django

# Setup Django with error handling
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings_render_free')
    django.setup()
    from django.contrib.auth.models import User
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    exit(1)

def create_admin():
    username = 'admin'
    email = 'admin@portfoliosuite.com'
    password = 'admin123'
    
    try:
        # Always try to get or create the user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"✅ CREATED superuser {username} with all permissions")
        else:
            # Update existing user to ensure all permissions are set
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.set_password(password)
            user.save()
            print(f"✅ UPDATED {username} to superuser with staff permissions")
        
        # Verify
        user = User.objects.get(username=username)
        print(f"✅ Verification:")
        print(f"   - Username: {user.username}")
        print(f"   - Is Active: {user.is_active}")
        print(f"   - Is Staff: {user.is_staff}")
        print(f"   - Is Superuser: {user.is_superuser}")
        print(f"   - Password set: {'Yes' if user.password else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = create_admin()
    if success:
        print("\n🎉 Admin user ready!")
        print("You can now login at /admin/ with:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("\n❌ Failed to create admin user")
