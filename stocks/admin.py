from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Stock, StockPrice, Portfolio, LoginAttempt, SupportMessage


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


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'priority', 'status', 'created_at_short', 'is_overdue_display', 'admin_responder_display']
    list_filter = ['status', 'priority', 'created_at', 'resolved_at']
    search_fields = ['subject', 'user__username', 'user__email', 'message', 'admin_response']
    ordering = ['-created_at']
    readonly_fields = ['user', 'created_at', 'updated_at', 'response_time_display']
    
    fieldsets = (
        ('Support Request', {
            'fields': ('user', 'subject', 'message', 'priority', 'created_at')
        }),
        ('Status & Response', {
            'fields': ('status', 'admin_response', 'admin_responder', 'resolved_at', 'updated_at')
        }),
        ('Metrics', {
            'fields': ('response_time_display',),
            'classes': ('collapse',)
        })
    )
    
    def created_at_short(self, obj):
        """Display shortened creation date"""
        return obj.created_at.strftime('%m/%d/%Y %H:%M')
    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'
    
    def is_overdue_display(self, obj):
        """Display overdue status with color coding"""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ OVERDUE</span>')
        else:
            return format_html('<span style="color: green;">✅ On Time</span>')
    is_overdue_display.short_description = 'SLA Status'
    
    def admin_responder_display(self, obj):
        """Display admin responder with fallback"""
        if obj.admin_responder:
            return obj.admin_responder.get_full_name() or obj.admin_responder.username
        return '-'
    admin_responder_display.short_description = 'Responder'
    
    def response_time_display(self, obj):
        """Display response time in a readable format"""
        if obj.response_time:
            total_seconds = int(obj.response_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "No response yet"
    response_time_display.short_description = 'Response Time'
    
    def save_model(self, request, obj, form, change):
        """Set admin_responder when admin responds"""
        if change and obj.admin_response and not obj.admin_responder:
            obj.admin_responder = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'admin_responder')
    
    # Custom actions
    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_closed']
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected messages as in progress"""
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f'{updated} message(s) marked as in progress.')
    mark_as_in_progress.short_description = "Mark as In Progress"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected messages as resolved"""
        now = timezone.now()
        for message in queryset:
            message.status = 'RESOLVED'
            if not message.resolved_at:
                message.resolved_at = now
            message.save()
        self.message_user(request, f'{len(queryset)} message(s) marked as resolved.')
    mark_as_resolved.short_description = "Mark as Resolved"
    
    def mark_as_closed(self, request, queryset):
        """Mark selected messages as closed"""
        now = timezone.now()
        for message in queryset:
            message.status = 'CLOSED'
            if not message.resolved_at:
                message.resolved_at = now
            message.save()
        self.message_user(request, f'{len(queryset)} message(s) marked as closed.')
    mark_as_closed.short_description = "Mark as Closed"
