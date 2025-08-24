from django.contrib import admin
from .models import Stock, StockPrice, Portfolio


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
