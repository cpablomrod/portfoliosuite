from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios', help_text="Owner of this portfolio transaction")
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


class LoginAttempt(models.Model):
    """Model to track login attempts for security purposes"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.username} - {status} - {self.timestamp}"
    
    @classmethod
    def is_account_locked(cls, username):
        """Check if account is locked due to failed attempts"""
        # Check last 3 attempts in the last 15 minutes
        cutoff_time = timezone.now() - timedelta(minutes=15)
        recent_attempts = cls.objects.filter(
            username=username,
            timestamp__gte=cutoff_time
        ).order_by('-timestamp')[:3]
        
        # If we have 3 recent attempts and all are failed, account is locked
        if len(recent_attempts) == 3 and all(not attempt.success for attempt in recent_attempts):
            return True, recent_attempts[0].timestamp + timedelta(minutes=15)
        
        return False, None
    
    @classmethod
    def get_failed_attempts_count(cls, username):
        """Get count of recent failed attempts"""
        cutoff_time = timezone.now() - timedelta(minutes=15)
        return cls.objects.filter(
            username=username,
            success=False,
            timestamp__gte=cutoff_time
        ).count()
    
    @classmethod
    def clear_attempts(cls, username):
        """Clear login attempts for a user (called on successful login)"""
        cutoff_time = timezone.now() - timedelta(hours=1)
        cls.objects.filter(username=username, timestamp__lt=cutoff_time).delete()


class SupportMessage(models.Model):
    """Model to store user support messages for admin review"""
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_messages', help_text="User who submitted the support message")
    subject = models.CharField(max_length=200, help_text="Brief subject line for the support message")
    message = models.TextField(help_text="Detailed description of the issue or question")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', help_text="Priority level of the support request")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN', help_text="Current status of the support request")
    admin_response = models.TextField(blank=True, help_text="Admin's response to the support message")
    admin_responder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_responses', help_text="Admin who responded to this message")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When the support request was resolved")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to set resolved_at when status changes to resolved"""
        if self.status in ['RESOLVED', 'CLOSED'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def response_time(self):
        """Calculate response time if admin has responded"""
        if self.admin_response and self.updated_at:
            return self.updated_at - self.created_at
        return None
    
    @property
    def is_overdue(self):
        """Check if support request is overdue based on priority"""
        if self.status in ['RESOLVED', 'CLOSED']:
            return False
        
        now = timezone.now()
        time_diff = now - self.created_at
        
        # Define SLA times based on priority
        sla_hours = {
            'URGENT': 2,
            'HIGH': 8,
            'MEDIUM': 24,
            'LOW': 72
        }
        
        max_hours = sla_hours.get(self.priority, 24)
        return time_diff.total_seconds() > (max_hours * 3600)
