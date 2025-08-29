from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import traceback


@csrf_exempt
@require_http_methods(["GET", "POST"])
def admin_health_check(request):
    """Simple health check for admin functionality"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check admin users
        admin_count = User.objects.filter(is_superuser=True).count()
        
        # Create admin if none exists
        if admin_count == 0:
            try:
                with transaction.atomic():
                    admin = User.objects.create_user(
                        username='admin',
                        email='admin@portfoliosuite.com',
                        password='HealthCheck2025!'
                    )
                    admin.is_staff = True
                    admin.is_superuser = True
                    admin.is_active = True
                    admin.save()
                    
                return JsonResponse({
                    'status': 'success',
                    'message': 'Admin user created successfully',
                    'admin_count': 1,
                    'credentials': {
                        'username': 'admin',
                        'password': 'HealthCheck2025!'
                    }
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Failed to create admin: {str(e)}'
                })
        
        # Admin exists
        admin_users = User.objects.filter(is_superuser=True)
        admin_info = []
        
        for admin in admin_users:
            admin_info.append({
                'username': admin.username,
                'email': admin.email,
                'is_active': admin.is_active,
                'is_staff': admin.is_staff,
                'is_superuser': admin.is_superuser,
                'last_login': str(admin.last_login) if admin.last_login else None
            })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Admin health check passed',
            'admin_count': admin_count,
            'admin_users': admin_info
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'traceback': traceback.format_exc()
        })


@csrf_exempt
def reset_admin_simple(request):
    """Simple admin reset endpoint"""
    try:
        username = 'admin'
        password = 'Simple2025!'
        
        with transaction.atomic():
            # Delete existing admin users to avoid conflicts
            User.objects.filter(username=username).delete()
            
            # Create fresh admin user
            admin = User.objects.create_user(
                username=username,
                email='admin@portfoliosuite.com',
                password=password
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_active = True
            admin.save()
        
        return HttpResponse(f"""
        <html>
        <body>
        <h1>✅ Admin User Reset Successfully</h1>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>Password:</strong> {password}</p>
        <p><a href="/admin/">Go to Admin Console</a></p>
        </body>
        </html>
        """, content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"""
        <html>
        <body>
        <h1>❌ Admin Reset Failed</h1>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        </body>
        </html>
        """, content_type='text/html')


@csrf_exempt
def comprehensive_admin_reset(request):
    """Comprehensive admin reset with full debugging"""
    try:
        from django.contrib.auth import authenticate
        from django.db import transaction
        import traceback
        
        username = 'admin'
        password = 'ComprehensiveReset2025!'
        
        # Step 1: Show current database info
        from django.conf import settings
        db_info = {
            'ENGINE': settings.DATABASES['default']['ENGINE'],
            'NAME': settings.DATABASES['default'].get('NAME', 'N/A'),
            'HOST': settings.DATABASES['default'].get('HOST', 'N/A'),
        }
        
        # Step 2: Delete all existing users with username 'admin'
        from django.contrib.auth.models import User
        deleted_users = User.objects.filter(username=username)
        deleted_count = deleted_users.count()
        deleted_users.delete()
        
        # Step 3: Create fresh admin user
        with transaction.atomic():
            admin = User.objects.create_user(
                username=username,
                email='admin@portfoliosuite.com',
                password=password
            )
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_active = True
            admin.save()
        
        # Step 4: Verify the user exists
        created_user = User.objects.get(username=username)
        user_info = {
            'id': created_user.id,
            'username': created_user.username,
            'email': created_user.email,
            'is_active': created_user.is_active,
            'is_staff': created_user.is_staff,
            'is_superuser': created_user.is_superuser,
            'password_hash': created_user.password[:50] + '...',
        }
        
        # Step 5: Test authentication
        test_auth = authenticate(username=username, password=password)
        auth_success = test_auth is not None
        
        # Step 6: Test password checking directly
        password_check = created_user.check_password(password)
        
        return HttpResponse(f"""
        <html>
        <head><title>Comprehensive Admin Reset</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>🔧 Comprehensive Admin Reset</h1>
        
        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>Database Information:</h2>
            <p><strong>Engine:</strong> {db_info['ENGINE']}</p>
            <p><strong>Name:</strong> {db_info['NAME']}</p>
            <p><strong>Host:</strong> {db_info['HOST']}</p>
        </div>
        
        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>Reset Results:</h2>
            <p>✅ Deleted {deleted_count} existing admin user(s)</p>
            <p>✅ Created new admin user</p>
            <p><strong>Username:</strong> <code>{username}</code></p>
            <p><strong>Password:</strong> <code>{password}</code></p>
        </div>
        
        <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>User Verification:</h2>
            <p><strong>User ID:</strong> {user_info['id']}</p>
            <p><strong>Username:</strong> {user_info['username']}</p>
            <p><strong>Email:</strong> {user_info['email']}</p>
            <p><strong>Active:</strong> {user_info['is_active']}</p>
            <p><strong>Staff:</strong> {user_info['is_staff']}</p>
            <p><strong>Superuser:</strong> {user_info['is_superuser']}</p>
            <p><strong>Password Hash:</strong> {user_info['password_hash']}</p>
        </div>
        
        <div style="background: {'#e8f5e9' if auth_success else '#ffebee'}; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>Authentication Tests:</h2>
            <p><strong>Django authenticate():</strong> {'✅ SUCCESS' if auth_success else '❌ FAILED'}</p>
            <p><strong>Direct password check:</strong> {'✅ SUCCESS' if password_check else '❌ FAILED'}</p>
        </div>
        
        <div style="margin: 30px 0;">
            <a href="/admin/" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔗 Go to Admin Console</a>
        </div>
        </body>
        </html>
        """, content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>❌ Comprehensive Admin Reset Failed</h1>
        <div style="background: #ffebee; padding: 20px; border-radius: 8px;">
            <p><strong>Error:</strong> {str(e)}</p>
            <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{traceback.format_exc()}</pre>
        </div>
        </body>
        </html>
        """, content_type='text/html')

@csrf_exempt
def ultra_admin_reset(request):
    """Ultra-simple admin reset with authentication test"""
    try:
        from django.contrib.auth import authenticate
        
        username = 'admin'
        password = 'UltraReset2025!'
        
        # Step 1: Delete all existing admin users
        deleted_count = User.objects.filter(username=username).delete()[0]
        
        # Step 2: Create fresh admin user with guaranteed password
        with transaction.atomic():
            admin = User()
            admin.username = username
            admin.email = 'admin@portfoliosuite.com'
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_active = True
            admin.set_password(password)  # This ensures proper hashing
            admin.save()
        
        # Step 3: Verify authentication works
        test_user = authenticate(username=username, password=password)
        auth_status = "✅ WORKING" if test_user else "❌ FAILED"
        
        return HttpResponse(f"""
        <html>
        <head><title>Ultra Admin Reset</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>🔧 Ultra Admin Reset Complete</h1>
        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>Admin Credentials:</h2>
            <p><strong>Username:</strong> <code>{username}</code></p>
            <p><strong>Password:</strong> <code>{password}</code></p>
            <p><strong>Authentication Test:</strong> {auth_status}</p>
        </div>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>Details:</h3>
            <p>• Deleted {deleted_count} existing admin user(s)</p>
            <p>• Created fresh admin user with proper permissions</p>
            <p>• Verified password hashing and authentication</p>
        </div>
        <div style="margin: 30px 0;">
            <a href="/admin/" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔗 Go to Admin Console</a>
            <a href="/admin-health/" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">📊 Health Check</a>
        </div>
        </body>
        </html>
        """, content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>❌ Ultra Admin Reset Failed</h1>
        <div style="background: #ffebee; padding: 20px; border-radius: 8px;">
            <p><strong>Error:</strong> {str(e)}</p>
            <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{traceback.format_exc()}</pre>
        </div>
        <p><a href="/admin-health/">Try Health Check</a></p>
        </body>
        </html>
        """, content_type='text/html')
