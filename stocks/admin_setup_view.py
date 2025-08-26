from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import connection
import os


def setup_admin_view(request):
    """
    Setup admin user for PostgreSQL database
    Access at: /setup-admin/
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "✅ PostgreSQL Connected"
    except Exception as e:
        db_status = f"❌ Database Error: {e}"
    
    try:
        # Check if admin exists
        admin_exists = User.objects.filter(username='admin').exists()
        total_users = User.objects.count()
        
        if admin_exists:
            # Update existing admin
            admin_user = User.objects.get(username='admin')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.email = 'admin@portfoliosuite.com'
            admin_user.set_password('admin123')
            admin_user.save()
            
            user_status = f"✅ UPDATED existing admin user"
        else:
            # Create new admin
            admin_user = User.objects.create_superuser('admin', 'admin@portfoliosuite.com', 'admin123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save()
            
            user_status = f"✅ CREATED new admin user"
        
        # Verify admin user
        admin_check = User.objects.get(username='admin')
        
        response_html = f"""
<html>
<head><title>Admin Setup Status</title></head>
<body style="font-family: monospace; padding: 20px;">
<h2>🔧 Admin Setup Status</h2>

<h3>Database Status:</h3>
<p>{db_status}</p>

<h3>User Creation:</h3>
<p>{user_status}</p>

<h3>Admin User Verification:</h3>
<ul>
    <li>Username: {admin_check.username}</li>
    <li>Email: {admin_check.email}</li>
    <li>Is Active: {admin_check.is_active}</li>
    <li>Is Staff: {admin_check.is_staff}</li>
    <li>Is Superuser: {admin_check.is_superuser}</li>
    <li>Password Hash: {admin_check.password[:50]}...</li>
    <li>Total Users in DB: {total_users}</li>
</ul>

<h3>🎯 Login Information:</h3>
<p><strong>Admin Console:</strong> <a href="/admin/">/admin/</a></p>
<p><strong>Username:</strong> admin</p>
<p><strong>Password:</strong> admin123</p>

<hr>
<p><em>✅ Admin user is ready for login!</em></p>
</body>
</html>
        """
        
        return HttpResponse(response_html)
        
    except Exception as e:
        error_html = f"""
<html>
<head><title>Admin Setup Error</title></head>
<body style="font-family: monospace; padding: 20px;">
<h2>❌ Admin Setup Error</h2>
<p><strong>Error:</strong> {str(e)}</p>
<p><strong>Database Status:</strong> {db_status}</p>
</body>
</html>
        """
        return HttpResponse(error_html, status=500)


def db_info_view(request):
    """
    Show database connection information
    Access at: /db-info/
    """
    try:
        # Get database info
        db_settings = {
            'ENGINE': connection.settings_dict.get('ENGINE', 'Unknown'),
            'NAME': connection.settings_dict.get('NAME', 'Unknown'),
            'HOST': connection.settings_dict.get('HOST', 'Unknown'),
            'PORT': connection.settings_dict.get('PORT', 'Unknown'),
            'USER': connection.settings_dict.get('USER', 'Unknown'),
        }
        
        # Test connection and get database version
        db_version = "Unknown"
        try:
            with connection.cursor() as cursor:
                # Try PostgreSQL version command
                if 'postgresql' in db_settings['ENGINE'].lower():
                    cursor.execute("SELECT version()")
                    result = cursor.fetchone()
                    db_version = result[0] if result else "PostgreSQL (version unknown)"
                # Try SQLite version command
                elif 'sqlite' in db_settings['ENGINE'].lower():
                    cursor.execute("SELECT sqlite_version()")
                    result = cursor.fetchone()
                    db_version = f"SQLite {result[0]}" if result else "SQLite (version unknown)"
                else:
                    db_version = "Unknown database type"
        except Exception as version_error:
            db_version = f"Version check failed: {version_error}"
        
        # Count users
        user_count = User.objects.count()
        all_users = User.objects.all().values_list('username', 'email', 'is_staff', 'is_superuser')
        
        response_html = f"""
<html>
<head><title>Database Information</title></head>
<body style="font-family: monospace; padding: 20px;">
<h2>🗄️ Database Information</h2>

<h3>Database Configuration:</h3>
<ul>
    <li>Engine: {db_settings['ENGINE']}</li>
    <li>Host: {db_settings['HOST']}</li>
    <li>Port: {db_settings['PORT']}</li>
    <li>Database: {db_settings['NAME']}</li>
    <li>User: {db_settings['USER']}</li>
    <li>Version: {db_version}</li>
</ul>

<h3>User Data:</h3>
<p>Total Users: {user_count}</p>

<table border="1" cellpadding="5">
    <tr><th>Username</th><th>Email</th><th>Staff</th><th>Superuser</th></tr>
"""
        
        for username, email, is_staff, is_superuser in all_users:
            response_html += f"<tr><td>{username}</td><td>{email}</td><td>{'✅' if is_staff else '❌'}</td><td>{'✅' if is_superuser else '❌'}</td></tr>"
        
        response_html += """
</table>

<hr>
<p><strong>📖 PostgreSQL Access:</strong></p>
<p>To access PostgreSQL management console:</p>
<ol>
    <li>Go to your Render Dashboard</li>
    <li>Find "portfoliosuite-db" database</li>
    <li>Click "Connect" to get connection details</li>
    <li>Use psql or any PostgreSQL client</li>
</ol>

</body>
</html>
        """
        
        return HttpResponse(response_html)
        
    except Exception as e:
        error_html = f"""
<html>
<head><title>Database Error</title></head>
<body style="font-family: monospace; padding: 20px;">
<h2>❌ Database Error</h2>
<p><strong>Error:</strong> {str(e)}</p>
</body>
</html>
        """
        return HttpResponse(error_html, status=500)


def env_debug_view(request):
    """
    Show environment variables for debugging
    Access at: /env-debug/
    """
    import os
    from django.conf import settings
    
    # Get key environment variables (without exposing secrets)
    env_vars = {
        'DJANGO_SETTINGS_MODULE': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not Set'),
        'DATABASE_URL': 'Present' if 'DATABASE_URL' in os.environ else 'Not Found',
        'SECRET_KEY': 'Present' if 'SECRET_KEY' in os.environ else 'Not Found',
    }
    
    # Check if DATABASE_URL starts with expected prefix
    if 'DATABASE_URL' in os.environ:
        db_url = os.environ.get('DATABASE_URL')
        if db_url.startswith('postgres://'):
            env_vars['DATABASE_URL_TYPE'] = 'PostgreSQL'
        elif db_url.startswith('sqlite://'):
            env_vars['DATABASE_URL_TYPE'] = 'SQLite'
        else:
            env_vars['DATABASE_URL_TYPE'] = 'Unknown'
        env_vars['DATABASE_URL_PREFIX'] = db_url[:30] + '...' if len(db_url) > 30 else db_url
    
    # Get Django database configuration
    db_config = settings.DATABASES['default']
    
    response_html = f"""
<html>
<head><title>Environment Debug</title></head>
<body style="font-family: monospace; padding: 20px;">
<h2>🐛 Environment Debug Information</h2>

<h3>Environment Variables:</h3>
<table border="1" cellpadding="5">
    <tr><th>Variable</th><th>Status</th></tr>
"""
    
    for key, value in env_vars.items():
        response_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    
    response_html += f"""
</table>

<h3>Django Database Configuration:</h3>
<table border="1" cellpadding="5">
    <tr><th>Setting</th><th>Value</th></tr>
    <tr><td>ENGINE</td><td>{db_config.get('ENGINE', 'Unknown')}</td></tr>
    <tr><td>NAME</td><td>{db_config.get('NAME', 'Unknown')}</td></tr>
    <tr><td>HOST</td><td>{db_config.get('HOST', 'Unknown')}</td></tr>
    <tr><td>PORT</td><td>{db_config.get('PORT', 'Unknown')}</td></tr>
    <tr><td>USER</td><td>{db_config.get('USER', 'Unknown')}</td></tr>
</table>

<h3>🔗 Other Debug URLs:</h3>
<ul>
    <li><a href="/setup-admin/">Setup Admin User</a></li>
    <li><a href="/db-info/">Database Information</a></li>
    <li><a href="/admin/">Admin Console</a></li>
</ul>

</body>
</html>
    """
    
    return HttpResponse(response_html)
