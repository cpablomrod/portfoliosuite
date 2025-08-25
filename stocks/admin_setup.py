from django.http import HttpResponse
from django.contrib.auth.models import User
import os


def create_admin_user(request):
    """
    Simple view to create admin user - ONLY FOR SETUP, REMOVE AFTER USE
    Access this at: /setup-admin/
    """
    if request.method == 'GET':
        try:
            username = 'admin'
            email = 'admin@portfoliosuite.com'
            password = 'admin123'
            
            # Check if admin user exists
            if User.objects.filter(username=username).exists():
                # Update existing user
                user = User.objects.get(username=username)
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.email = email
                user.set_password(password)
                user.save()
                message = f"✅ UPDATED admin user with staff permissions\n"
            else:
                # Create new superuser
                user = User.objects.create_superuser(username, email, password)
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
                message = f"✅ CREATED new admin superuser\n"
            
            # Verify the user
            user.refresh_from_db()
            verification = f"""
Admin User Details:
- Username: {user.username}
- Email: {user.email}
- Is Active: {user.is_active}
- Is Staff: {user.is_staff}
- Is Superuser: {user.is_superuser}
- Password Hash: {user.password[:50]}...

You can now login at: /admin/
Username: admin
Password: admin123

⚠️ IMPORTANT: Remove this setup URL after use for security!
"""
            
            return HttpResponse(f"<pre>{message}{verification}</pre>", content_type="text/html")
            
        except Exception as e:
            return HttpResponse(f"<pre>❌ Error creating admin user: {str(e)}</pre>", content_type="text/html")
    
    return HttpResponse("<pre>❌ Only GET requests allowed</pre>", content_type="text/html")
