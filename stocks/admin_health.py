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
