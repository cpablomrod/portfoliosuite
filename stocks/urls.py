from django.urls import path
from . import views
from . import auth_views
from .real_data_service import real_historical_chart_data
from .debug_login import debug_login_status
from .debug_views import debug_lockout_view
from django.contrib.auth import views as django_auth_views

urlpatterns = [
    # Authentication URLs (custom secure login)
    path('accounts/login/', auth_views.secure_login_view, name='login'),
    path('accounts/logout/', django_auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_reset/', django_auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', django_auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', django_auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', django_auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('register/', auth_views.register_view, name='register'),
    path('profile/', auth_views.profile_view, name='profile'),
    
    # Portfolio URLs (require authentication)
    path('', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('update-prices/', views.update_prices, name='update_prices'),
    path('run-simulation/', views.run_simulation, name='run_simulation'),
    path('chart-data/', views.chart_data, name='chart_data'),
    path('api/performance-since-inception/', views.performance_since_inception_data, name='performance_since_inception_data'),
    path('api/stock-search/', views.stock_search, name='stock_search'),
    path('api/stock-price/', views.get_stock_price, name='get_stock_price'),
    path('api/sector-allocation/', views.sector_allocation_data, name='sector_allocation_data'),
    path('change-portfolio/', views.change_portfolio, name='change_portfolio'),
    path('generate-report/', views.generate_portfolio_report, name='generate_portfolio_report'),
    path('api/real-historical-data/', real_historical_chart_data, name='real_historical_chart_data'),
    
    # User management URLs
    path('change-user/', auth_views.change_user_view, name='change_user'),
    path('goodbye/', auth_views.goodbye_view, name='goodbye'),
    
    # Debug URLs
    path('debug-login/', debug_login_status, name='debug_login'),
    path('debug-lockout/', debug_lockout_view, name='debug_lockout'),
    
    # Admin Health URLs
    path('admin-health/', views.admin_health_check, name='admin_health_check'),
    path('reset-admin-simple/', views.reset_admin_simple, name='reset_admin_simple'),
    
    # Support URLs
    path('support/create/', views.create_support_message, name='create_support_message'),
    path('support/messages/', views.get_user_support_messages, name='get_user_support_messages'),
    path('support/history/', views.support_history, name='support_history'),
]
