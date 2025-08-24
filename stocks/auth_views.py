from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django import forms
from .models import LoginAttempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with email confirmation and names"""
    
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    email_confirm = forms.EmailField(
        required=True,
        help_text='Please confirm your email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Confirm Email'
    )
    
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        help_text='Optional.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        help_text='Optional.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean_email_confirm(self):
        """Validate that email confirmation matches the original email"""
        email = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')
        
        if email and email_confirm and email != email_confirm:
            raise forms.ValidationError("Email addresses don't match.")
        return email_confirm
    
    def clean_email(self):
        """Validate that email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        
        # Buffer overflow protection for email field
        from .security.buffer_protection import validate_input_length
        validate_input_length(email or '', max_length=254, field_name="Email")
        
        return email
    
    def clean_username(self):
        """Validate username with buffer overflow protection"""
        username = self.cleaned_data.get('username')
        
        # Buffer overflow protection for username field
        from .security.buffer_protection import validate_input_length
        validate_input_length(username or '', max_length=150, field_name="Username")
        
        return username
    
    def clean_first_name(self):
        """Validate first name with buffer overflow protection"""
        first_name = self.cleaned_data.get('first_name', '')
        
        # Buffer overflow protection
        from .security.buffer_protection import validate_input_length
        validate_input_length(first_name, max_length=30, field_name="First name")
        
        return first_name
    
    def clean_last_name(self):
        """Validate last name with buffer overflow protection"""
        last_name = self.cleaned_data.get('last_name', '')
        
        # Buffer overflow protection
        from .security.buffer_protection import validate_input_length
        validate_input_length(last_name, max_length=30, field_name="Last name")
        
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            login(request, user)  # Automatically log in the user
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def profile_view(request):
    """User profile view"""
    return render(request, 'registration/profile.html', {
        'user': request.user
    })


@login_required
def change_user_view(request):
    """Change user view - logs out current user and redirects to login"""
    username = request.user.username
    logout(request)
    messages.info(request, f'You have been logged out. Please log in with a different account.')
    return redirect('login')


def secure_login_view(request):
    """Secure login view with account lockout protection"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Initialize form
    form = AuthenticationForm()
    account_locked = False
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        # Check if account is locked before processing form
        if username:
            is_locked, unlock_time = LoginAttempt.is_account_locked(username)
            
            if is_locked and unlock_time:
                account_locked = True
                time_remaining = unlock_time - timezone.now()
                minutes_remaining = max(1, int(time_remaining.total_seconds() / 60))
                messages.error(
                    request, 
                    f'🔒 Account "{username}" is temporarily locked due to too many failed login attempts. '
                    f'Please try again in {minutes_remaining} minute{"s" if minutes_remaining != 1 else ""}.'
                )
                
                # Still record this as a failed attempt
                from .auth_backends import get_client_ip, get_user_agent
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    success=False
                )
                
                return render(request, 'registration/login.html', {
                    'form': AuthenticationForm(),
                    'account_locked': True,
                    'unlock_time': unlock_time,
                    'failed_attempts': 3,
                    'locked_username': username
                })
        
        # If not locked, process the form normally
        form = AuthenticationForm(request, data=request.POST)
        
        # Show warning for approaching lockout (before form validation)
        if username:
            failed_attempts = LoginAttempt.get_failed_attempts_count(username)
            if failed_attempts == 1:
                messages.warning(
                    request,
                    f'⚠️ Warning: 2 attempts remaining before account lockout for "{username}".'
                )
            elif failed_attempts == 2:
                messages.warning(
                    request,
                    f'⚠️ Warning: 1 attempt remaining before account lockout for "{username}".'
                )
        
        if form.is_valid():
            # Successful login
            user = form.get_user()
            
            # Record successful attempt
            from .auth_backends import get_client_ip, get_user_agent
            LoginAttempt.objects.create(
                username=username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=True
            )
            
            # Clear old failed attempts
            LoginAttempt.clear_attempts(username)
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            # Form is invalid (wrong password)
            if username:
                # Record failed attempt
                from .auth_backends import get_client_ip, get_user_agent
                LoginAttempt.objects.create(
                    username=username,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    success=False
                )
                
                # Check if this was the 3rd failed attempt
                failed_attempts = LoginAttempt.get_failed_attempts_count(username)
                if failed_attempts >= 3:
                    messages.error(
                        request, 
                        f'🔒 Account "{username}" has been locked for 15 minutes due to too many failed login attempts.'
                    )
                    account_locked = True
                else:
                    remaining = 3 - failed_attempts
                    messages.error(
                        request, 
                        f'❌ Invalid username or password. {remaining} attempt{"s" if remaining != 1 else ""} remaining before lockout.'
                    )
            else:
                messages.error(request, '❌ Please enter a username and password.')
    
    return render(request, 'registration/login.html', {
        'form': form,
        'account_locked': account_locked
    })


@login_required
def goodbye_view(request):
    """Goodbye view - shows goodbye message and logs out user"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    return render(request, 'registration/goodbye.html', {
        'user_name': user_name
    })
