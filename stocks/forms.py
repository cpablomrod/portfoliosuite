from django import forms
from django.utils import timezone
from .models import Portfolio, Stock
from .security.buffer_protection import (
    validate_input_length, 
    validate_numeric_input,
    SecureCharField,
    SecureNumericField
)


class AddTransactionForm(forms.ModelForm):
    """Form for adding a new stock transaction"""
    
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., AAPL, GOOGL',
            'class': 'form-control',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Stock symbol (will be converted to uppercase)"
    )
    
    price_per_share = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Will be fetched automatically',
            'step': '0.01',
            'readonly': True
        }),
        help_text="Current market price (auto-filled)"
    )
    
    class Meta:
        model = Portfolio
        fields = ['symbol', 'transaction_type', 'quantity', 'price_per_share', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100',
                'step': '1',
                'min': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this transaction...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove stock field since we're using symbol
        if 'stock' in self.fields:
            del self.fields['stock']
    
    def clean_symbol(self):
        symbol = self.cleaned_data['symbol'].upper().strip()
        if not symbol:
            raise forms.ValidationError("Stock symbol is required")
        
        # Buffer overflow protection
        validate_input_length(symbol, max_length=10, field_name="Stock symbol")
        
        return symbol
    
    def clean_notes(self):
        notes = self.cleaned_data.get('notes', '')
        # Buffer overflow protection for notes field
        validate_input_length(notes, max_length=1000, field_name="Notes")
        return notes
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            # Validate numeric input to prevent overflow
            validate_numeric_input(
                str(quantity), 
                min_val=0.0001, 
                max_val=999999999.99, 
                field_name="Quantity"
            )
        return quantity
    
    def clean_price_per_share(self):
        price = self.cleaned_data.get('price_per_share')
        if price is not None:
            # Validate numeric input to prevent overflow
            validate_numeric_input(
                str(price), 
                min_val=0.01, 
                max_val=999999.99, 
                field_name="Price per share"
            )
        return price
    
    def save(self, portfolio_name='My Investment Portfolio', user=None, commit=True):
        try:
            instance = super().save(commit=False)
            
            # Get or create the stock based on the symbol
            symbol = self.cleaned_data['symbol']
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={'company_name': ''}
            )
            instance.stock = stock
            
            # Set the user (required)
            if user:
                instance.user = user
            else:
                raise ValueError("User is required for transaction")
            
            # Set the portfolio name
            instance.portfolio_name = portfolio_name
            
            # Use provided price or default to 0.00
            price = self.cleaned_data.get('price_per_share')
            if price is not None and price > 0:
                instance.price_per_share = price
            else:
                instance.price_per_share = 0.00  # Default price - will be updated when prices are fetched
                
            instance.transaction_date = timezone.now().date()  # Default to today
            
            if commit:
                instance.save()
            
            return instance
        except Exception as e:
            # Only log detailed errors in development
            import os
            if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('settings'):
                import traceback
                print(f"ERROR in form save: {e}")
                print(f"TRACEBACK: {traceback.format_exc()}")
            raise


class SimulationForm(forms.Form):
    """Form for running historical simulations"""
    
    symbols = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., AAPL, GOOGL, MSFT',
            'class': 'form-control'
        }),
        help_text="Enter stock symbols separated by commas"
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Start date for simulation"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="End date for simulation"
    )
    
    initial_investment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10000.00',
            'step': '0.01'
        }),
        help_text="Total amount to invest (will be split equally among stocks)"
    )
    
    def clean_symbols(self):
        symbols = self.cleaned_data['symbols']
        # Split by comma and clean up
        symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
        if not symbol_list:
            raise forms.ValidationError("At least one stock symbol is required")
        return symbol_list
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("Start date must be before end date")
            
            if end_date > timezone.now().date():
                raise forms.ValidationError("End date cannot be in the future")
        
        return cleaned_data
