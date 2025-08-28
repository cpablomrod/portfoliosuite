from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Reset admin user password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='AdminReset2025!',
            help='New password for admin user'
        )

    def handle(self, *args, **options):
        password = options['password']
        
        try:
            with transaction.atomic():
                # Get or create admin user
                user, created = User.objects.get_or_create(
                    username='admin',
                    defaults={
                        'email': 'admin@portfoliosuite.com',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'first_name': 'Admin',
                        'last_name': 'User'
                    }
                )
                
                # Set the password
                user.set_password(password)
                
                # Ensure proper permissions
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.email = 'admin@portfoliosuite.com'
                
                # Save the user
                user.save()
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created new admin user: {user.username}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Updated existing admin user: {user.username}')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'🔑 Password set to: {password}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'🔗 Login at: /admin/')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
            raise e
