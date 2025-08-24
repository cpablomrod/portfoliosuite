from django.urls import path
from . import views
from . import auth_views
from .real_data_service import real_historical_chart_data

urlpatterns = [
    # Authentication URLs
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
]
