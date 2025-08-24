from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django import forms
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
        return email

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


@login_required
def goodbye_view(request):
    """Goodbye view - shows goodbye message and logs out user"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    return render(request, 'registration/goodbye.html', {
        'user_name': user_name
    })
