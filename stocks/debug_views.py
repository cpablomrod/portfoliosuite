from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import LoginAttempt


def debug_lockout_view(request):
    """Debug view to test lockout message display"""
    
    # Test data
    test_username = 'debug_test_user'
    
    # Add some test messages to verify message display works
    messages.success(request, '✅ Success message test')
    messages.warning(request, '⚠️ Warning message test')
    messages.error(request, '🔒 Error message test - Account locked simulation')
    messages.info(request, 'ℹ️ Info message test')
    
    # Check lockout status of a real user
    lockout_info = {}
    for username in ['pedrosalas', 'testuserlock']:
        is_locked, unlock_time = LoginAttempt.is_account_locked(username)
        failed_count = LoginAttempt.get_failed_attempts_count(username)
        lockout_info[username] = {
            'is_locked': is_locked,
            'unlock_time': unlock_time,
            'failed_attempts': failed_count
        }
    
    return render(request, 'debug/lockout_test.html', {
        'lockout_info': lockout_info,
        'current_time': timezone.now()
    })
