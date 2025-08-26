"""
Render Free Tier settings for Portfolio Suite (uses PostgreSQL for data persistence)
"""
import os
from .settings import *

# Security settings for production
DEBUG = False
ALLOWED_HOSTS = [
    '*.onrender.com',  # Render deployment
    'portfoliosuite.onrender.com',  # Your specific domain
]

# Use PostgreSQL for production (persists data between deployments)
# Render provides a free PostgreSQL database
import dj_database_url

# Debug: Print database URL info
print(f"🔍 DATABASE_URL present: {'DATABASE_URL' in os.environ}")
if 'DATABASE_URL' in os.environ:
    db_url = os.environ.get('DATABASE_URL')
    print(f"🔍 DATABASE_URL starts with: {db_url[:50]}..." if len(db_url) > 50 else f"🔍 DATABASE_URL: {db_url}")
else:
    print("❌ No DATABASE_URL found in environment")

if 'DATABASE_URL' in os.environ:
    try:
        # Use PostgreSQL from Render
        parsed_db = dj_database_url.parse(os.environ.get('DATABASE_URL'))
        print(f"✅ PostgreSQL database parsed successfully: {parsed_db['ENGINE']}")
        DATABASES = {
            'default': parsed_db
        }
    except Exception as e:
        print(f"❌ Failed to parse DATABASE_URL: {e}")
        print("🔄 Falling back to manual PostgreSQL config")
        # Try manual PostgreSQL config as backup
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DATABASE_NAME', 'portfoliosuite'),
                'USER': os.environ.get('DATABASE_USER', 'portfoliosuite'),
                'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
                'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
                'PORT': os.environ.get('DATABASE_PORT', '5432'),
            }
        }
else:
    print("⚠️ No DATABASE_URL found - trying manual PostgreSQL configuration")
    
    # Check if we have individual PostgreSQL environment variables
    pg_vars = {
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USER'), 
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
    
    if pg_vars['HOST'] and pg_vars['USER'] and pg_vars['PASSWORD']:
        print("✅ Found individual PostgreSQL environment variables")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': pg_vars['NAME'] or 'portfoliosuite',
                'USER': pg_vars['USER'],
                'PASSWORD': pg_vars['PASSWORD'],
                'HOST': pg_vars['HOST'],
                'PORT': pg_vars['PORT'],
            }
        }
    else:
        print("❌ No PostgreSQL configuration found at all")
        print("⚠️ IMPORTANT: PostgreSQL database service is missing!")
        print("🔄 Using SQLite temporarily - data will not persist between deployments")
        print("📝 Action required: Create PostgreSQL database service in Render dashboard")
        
        # Temporary SQLite fallback with warning
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
        
        # Set a flag to show database warning in admin
        SHOW_DATABASE_WARNING = True

# Add whitenoise to middleware if not already there
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Use basic static files storage to avoid manifest issues
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Additional static files settings for Render
if os.path.exists(os.path.join(BASE_DIR, 'static')):
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]

# Whitenoise settings
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Email configuration (for password reset)
# Use console backend if no email credentials provided (development/testing)
if os.environ.get('EMAIL_HOST_USER') and os.environ.get('EMAIL_HOST_PASSWORD'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    
    # Support multiple email providers
    email_provider = os.environ.get('EMAIL_PROVIDER', 'brevo').lower()
    
    if email_provider == 'brevo':
        EMAIL_HOST = 'smtp-relay.brevo.com'
    elif email_provider == 'gmail':
        EMAIL_HOST = 'smtp.gmail.com'
    elif email_provider == 'outlook':
        EMAIL_HOST = 'smtp-mail.outlook.com'
    else:
        EMAIL_HOST = 'smtp-relay.brevo.com'  # Default to Brevo
    
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
else:
    # Fallback to console backend (emails will appear in logs)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@portfoliosuite.com')

# Alpha Vantage API Key (for stock data)
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')

# Django Secret Key
SECRET_KEY = os.environ.get('SECRET_KEY')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'stocks.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
