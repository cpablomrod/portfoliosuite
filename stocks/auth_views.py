from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django import forms
from .models import LoginAttempt, UserProfile
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
            
            # Create UserProfile for the new user
            try:
                UserProfile.objects.create(
                    user=user,
                    has_completed_onboarding=False
                )
            except Exception as e:
                # Log the error but don't prevent registration
                print(f"Error creating UserProfile for {username}: {e}")
            
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
    
    try:
        # Initialize variables
        form = AuthenticationForm()
        account_locked = False
        
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            
            # Check if account is locked FIRST - before any form processing
            if username:
                try:
                    is_locked, unlock_time = LoginAttempt.is_account_locked(username)
                    
                    if is_locked and unlock_time:
                        # Account is locked - show lockout message and prevent login
                        time_remaining = unlock_time - timezone.now()
                        minutes_remaining = max(1, int(time_remaining.total_seconds() / 60))
                        messages.error(
                            request, 
                            f'Account "{username}" is temporarily locked. '
                            f'Please try again in {minutes_remaining} minutes.'
                        )
                        
                        # Record this attempt as a failed login to locked account
                        try:
                            from .auth_backends import get_client_ip, get_user_agent
                            LoginAttempt.objects.create(
                                username=username,
                                ip_address=get_client_ip(request),
                                user_agent=get_user_agent(request),
                                success=False
                            )
                        except Exception:
                            pass  # Don't let logging failures break login
                        
                        # Return immediately with locked account status
                        return render(request, 'registration/login.html', {
                            'form': AuthenticationForm(),  # Fresh empty form
                            'account_locked': True,
                            'unlock_time': unlock_time,
                            'failed_attempts': 3,
                            'locked_username': username
                        })
                except Exception:
                    # If lockout check fails, continue with normal login
                    pass
            
            # Account is not locked - proceed with normal login flow
            form = AuthenticationForm(request, data=request.POST)
            
            if form.is_valid():
                # Successful login
                user = form.get_user()
                
                # Record successful attempt (but don't let it break login)
                try:
                    from .auth_backends import get_client_ip, get_user_agent
                    LoginAttempt.objects.create(
                        username=username,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        success=True
                    )
                    # Clear old failed attempts
                    LoginAttempt.clear_attempts(username)
                except Exception:
                    pass  # Don't let logging failures break login
                
                login(request, user)
                try:
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                except Exception:
                    pass  # Don't let message failures break login
                return redirect('dashboard')
            else:
                # Form validation failed (wrong credentials)
                if username:
                    try:
                        # Record failed attempt
                        from .auth_backends import get_client_ip, get_user_agent
                        LoginAttempt.objects.create(
                            username=username,
                            ip_address=get_client_ip(request),
                            user_agent=get_user_agent(request),
                            success=False
                        )
                        
                        # Check if this failed attempt triggers lockout
                        failed_attempts = LoginAttempt.get_failed_attempts_count(username)
                        if failed_attempts >= 3:
                            # Account just got locked with this attempt
                            messages.error(
                                request, 
                                f'Account "{username}" has been locked for 15 minutes due to too many failed login attempts.'
                            )
                            account_locked = True
                            
                            # Calculate unlock time for the newly locked account
                            unlock_time = timezone.now() + timedelta(minutes=15)
                            
                            return render(request, 'registration/login.html', {
                                'form': AuthenticationForm(),  # Fresh empty form
                                'account_locked': True,
                                'unlock_time': unlock_time,
                                'failed_attempts': failed_attempts,
                                'locked_username': username
                            })
                        else:
                            # Show remaining attempts warning
                            remaining = 3 - failed_attempts
                            messages.error(
                                request, 
                                f'Invalid username or password. {remaining} attempts remaining.'
                            )
                    except Exception:
                        # If attempt logging fails, just show generic error
                        messages.error(request, 'Invalid username or password.')
                else:
                    messages.error(request, 'Please enter a username and password.')
        
        return render(request, 'registration/login.html', {
            'form': form,
            'account_locked': account_locked
        })
    except Exception as e:
        # If anything goes wrong, fall back to basic Django login
        import os
        if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('settings'):
            print(f"Error in secure login view: {e}")
        
        # Return basic login form
        form = AuthenticationForm()
        if request.method == 'POST':
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return redirect('dashboard')
        
        return render(request, 'registration/login.html', {
            'form': form,
            'account_locked': False
        })


@login_required
def goodbye_view(request):
    """Goodbye view - shows goodbye message and logs out user"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    return render(request, 'registration/goodbye.html', {
        'user_name': user_name
    })
