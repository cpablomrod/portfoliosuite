from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from .models import LoginAttempt
from django.utils import timezone

def debug_login_status(request):
    """Debug view to show current login attempt status"""
    username = request.GET.get('username', 'pedrosalas')
    
    # Get lockout status
    is_locked, unlock_time = LoginAttempt.is_account_locked(username)
    failed_attempts = LoginAttempt.get_failed_attempts_count(username)
    
    # Get recent attempts
    recent_attempts = LoginAttempt.objects.filter(username=username).order_by('-timestamp')[:5]
    
    html = f"""
    <h1>Debug Login Status</h1>
    <p><strong>Username:</strong> {username}</p>
    <p><strong>Account Locked:</strong> {is_locked}</p>
    <p><strong>Failed Attempts (last 15 min):</strong> {failed_attempts}</p>
    <p><strong>Current Time:</strong> {timezone.now()}</p>
    {f'<p><strong>Unlock Time:</strong> {unlock_time}</p>' if unlock_time else ''}
    
    <h2>Recent Attempts:</h2>
    <ul>
    """
    
    for attempt in recent_attempts:
        status = "SUCCESS" if attempt.success else "FAILED"
        html += f"<li>{status} - {attempt.timestamp}</li>"
    
    html += """
    </ul>
    
    <h2>Test Messages:</h2>
    """
    
    # Add test messages
    messages.success(request, "This is a SUCCESS message")
    messages.error(request, "This is an ERROR message") 
    messages.warning(request, "This is a WARNING message")
    
    if is_locked:
        time_remaining = unlock_time - timezone.now()
        minutes_remaining = max(1, int(time_remaining.total_seconds() / 60))
        messages.error(request, f'🔒 Account "{username}" is locked for {minutes_remaining} more minutes!')
    
    return render(request, 'debug_login.html', {
        'username': username,
        'is_locked': is_locked,
        'failed_attempts': failed_attempts,
        'unlock_time': unlock_time,
        'recent_attempts': recent_attempts
    })
