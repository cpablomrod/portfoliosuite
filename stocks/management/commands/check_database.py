from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Check database tables and models'

    def handle(self, *args, **options):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS('✅ Database connection successful')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {e}')
            )
            return

        # Check if all models have corresponding tables
        stock_models = apps.get_app_config('stocks').get_models()
        
        with connection.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """ if connection.vendor == 'postgresql' else """
                SELECT name 
                FROM sqlite_master 
                WHERE type='table'
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f'📋 Found {len(existing_tables)} tables in database')
            
            for model in stock_models:
                table_name = model._meta.db_table
                if table_name in existing_tables:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {model.__name__} -> {table_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {model.__name__} -> {table_name} (MISSING)')
                    )

        # Check specific SupportMessage model
        try:
            from stocks.models import SupportMessage
            count = SupportMessage.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'✅ SupportMessage model accessible, {count} records')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ SupportMessage model error: {e}')
            )
