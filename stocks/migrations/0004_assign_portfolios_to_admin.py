from django.db import migrations
from django.contrib.auth.models import User


def assign_portfolios_to_admin(apps, schema_editor):
    """Assign all existing portfolio records to the admin user"""
    Portfolio = apps.get_model('stocks', 'Portfolio')
    
    # Get or create admin user (should already exist)
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        # Create admin user if it doesn't exist
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@portfoliosuite.com',
            is_staff=True,
            is_superuser=True
        )
    
    # Assign all existing portfolios to admin user
    Portfolio.objects.filter(user__isnull=True).update(user=admin_user)


def reverse_assign_portfolios(apps, schema_editor):
    """Reverse migration - set all portfolio users to null"""
    Portfolio = apps.get_model('stocks', 'Portfolio')
    Portfolio.objects.all().update(user=None)


class Migration(migrations.Migration):
    dependencies = [
        ('stocks', '0003_portfolio_user'),
    ]

    operations = [
        migrations.RunPython(
            assign_portfolios_to_admin,
            reverse_assign_portfolios,
        ),
    ]
