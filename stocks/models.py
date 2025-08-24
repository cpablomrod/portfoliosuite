from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Stock(models.Model):
    """Model to store stock information"""
    symbol = models.CharField(max_length=10, unique=True, help_text="Stock symbol (e.g., AAPL, GOOGL)")
    company_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"


class StockPrice(models.Model):
    """Model to store historical stock prices"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['stock', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.date} - ${self.close_price}"


class Portfolio(models.Model):
    """Model to store stock purchases/transactions"""
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    portfolio_name = models.CharField(max_length=100, default='My Investment Portfolio', help_text="Name of the portfolio this transaction belongs to")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES, default='BUY')
    quantity = models.DecimalField(max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    transaction_date = models.DateField()
    notes = models.TextField(blank=True, help_text="Optional notes about this transaction")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.stock.symbol} @ ${self.price_per_share}"
    
    @property
    def total_value(self):
        """Calculate total value of this transaction"""
        return self.quantity * self.price_per_share
