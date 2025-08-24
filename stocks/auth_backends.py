from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from .models import LoginAttempt


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


class SecureModelBackend(ModelBackend):
    """Custom authentication backend with login attempt tracking"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        # Check if account is locked
        is_locked, unlock_time = LoginAttempt.is_account_locked(username)
        if is_locked:
            # Account is locked, don't even attempt authentication
            self._record_attempt(request, username, success=False)
            return None
        
        # Try to authenticate with Django's default backend
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Record failed attempt for non-existent user to prevent username enumeration
            self._record_attempt(request, username, success=False)
            return None
        
        if user.check_password(password) and user.is_active:
            # Successful login
            self._record_attempt(request, username, success=True)
            # Clear old failed attempts on successful login
            LoginAttempt.clear_attempts(username)
            return user
        else:
            # Failed login
            self._record_attempt(request, username, success=False)
            return None
    
    def _record_attempt(self, request, username, success):
        """Record login attempt in database"""
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
        else:
            ip_address = '127.0.0.1'
            user_agent = ''
        
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
