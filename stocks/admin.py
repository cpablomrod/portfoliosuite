from django.contrib import admin
from .models import Stock, StockPrice, Portfolio, LoginAttempt


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'company_name', 'created_at', 'updated_at']
    search_fields = ['symbol', 'company_name']
    list_filter = ['created_at']
    ordering = ['symbol']


@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'close_price', 'volume']
    list_filter = ['stock', 'date']
    search_fields = ['stock__symbol']
    ordering = ['-date']
    readonly_fields = ['created_at']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['stock', 'transaction_type', 'quantity', 'price_per_share', 'transaction_date', 'total_value']
    list_filter = ['transaction_type', 'transaction_date', 'stock']
    search_fields = ['stock__symbol', 'notes']
    ordering = ['-transaction_date', '-created_at']
    readonly_fields = ['created_at', 'total_value']
    
    def total_value(self, obj):
        return f"${obj.total_value:.2f}"
    total_value.short_description = 'Total Value'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'success', 'timestamp', 'user_agent_short']
    list_filter = ['success', 'timestamp']
    search_fields = ['username', 'ip_address']
    ordering = ['-timestamp']
    readonly_fields = ['username', 'ip_address', 'user_agent', 'success', 'timestamp']
    
    def user_agent_short(self, obj):
        """Display shortened user agent for better readability"""
        if len(obj.user_agent) > 50:
            return obj.user_agent[:50] + '...'
        return obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        """Disable adding login attempts manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing login attempts"""
        return False
