"""
URL configuration for portfolio_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from stocks.admin_setup_view import setup_admin_view, db_info_view, env_debug_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('setup-admin/', setup_admin_view, name='setup_admin'),
    path('db-info/', db_info_view, name='db_info'),
    path('env-debug/', env_debug_view, name='env_debug'),
    # Remove built-in auth URLs to avoid conflicts with custom secure login
    # path('accounts/', include('django.contrib.auth.urls')),  # Commented out
    path('', include('stocks.urls')),
]
