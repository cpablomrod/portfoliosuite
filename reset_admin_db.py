#!/usr/bin/env python
"""
Direct database password reset for admin user
This bypasses Django ORM to ensure the password is actually set
"""
import os
import django
from django.contrib.auth.hashers import make_password

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings_render_free')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

def reset_admin_password_direct():
    try:
        username = 'admin'
        password = 'DirectReset2025!'
        email = 'admin@portfoliosuite.com'
        
        # Hash the password using Django's hasher
        hashed_password = make_password(password)
        
        print(f"🔑 Resetting password for user: {username}")
        print(f"🔐 New password will be: {password}")
        print(f"🏗️ Hashed password: {hashed_password[:50]}...")
        
        # Use raw SQL to ensure the update happens
        with connection.cursor() as cursor:
            # First, check if user exists
            cursor.execute(
                "SELECT id, username, is_staff, is_superuser, is_active FROM auth_user WHERE username = %s",
                [username]
            )
            result = cursor.fetchone()
            
            if result:
                user_id, db_username, is_staff, is_superuser, is_active = result
                print(f"✅ Found existing user:")
                print(f"   - ID: {user_id}")
                print(f"   - Username: {db_username}")
                print(f"   - Is Staff: {is_staff}")
                print(f"   - Is Superuser: {is_superuser}")
                print(f"   - Is Active: {is_active}")
                
                # Update the user with new password and ensure all permissions
                cursor.execute("""
                    UPDATE auth_user 
                    SET password = %s, 
                        is_staff = true, 
                        is_superuser = true, 
                        is_active = true,
                        email = %s
                    WHERE username = %s
                """, [hashed_password, email, username])
                
                print(f"✅ Updated user {username} with new password and permissions")
                
            else:
                print(f"❌ User {username} not found, creating new user...")
                
                # Create new superuser with raw SQL
                cursor.execute("""
                    INSERT INTO auth_user 
                    (username, email, password, is_staff, is_superuser, is_active, date_joined, first_name, last_name)
                    VALUES (%s, %s, %s, true, true, true, NOW(), '', '')
                """, [username, email, hashed_password])
                
                print(f"✅ Created new superuser {username}")
            
            # Verify the update
            cursor.execute(
                "SELECT username, is_staff, is_superuser, is_active, email FROM auth_user WHERE username = %s",
                [username]
            )
            result = cursor.fetchone()
            
            if result:
                db_username, is_staff, is_superuser, is_active, db_email = result
                print(f"\n🔍 Verification:")
                print(f"   - Username: {db_username}")
                print(f"   - Email: {db_email}")
                print(f"   - Is Staff: {is_staff}")
                print(f"   - Is Superuser: {is_superuser}")
                print(f"   - Is Active: {is_active}")
                
                if is_staff and is_superuser and is_active:
                    print("\n🎉 SUCCESS! Admin user is properly configured")
                    print(f"🔑 Login credentials:")
                    print(f"   Username: {username}")
                    print(f"   Password: {password}")
                    return True
                else:
                    print("\n❌ ERROR: User permissions not set correctly")
                    return False
            else:
                print("\n❌ ERROR: Could not verify user creation/update")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = reset_admin_password_direct()
    if success:
        print("\n🚀 You can now login to /admin/ with:")
        print("   Username: admin")
        print("   Password: DirectReset2025!")
    else:
        print("\n❌ Password reset failed")
