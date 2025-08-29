from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Force reset admin user with guaranteed password'

    def handle(self, *args, **options):
        try:
            # Force delete all admin users
            User.objects.filter(username='admin').delete()
            
            # Create completely fresh admin user
            with transaction.atomic():
                # Use create_user to ensure proper password hashing
                admin = User.objects.create_user(
                    username='admin',
                    email='admin@portfoliosuite.com',
                    password='ForceReset2025!'
                )
                
                # Set all required permissions
                admin.is_staff = True
                admin.is_superuser = True
                admin.is_active = True
                admin.save()
                
                # Double-check password is set correctly
                admin.set_password('ForceReset2025!')
                admin.save()
                
                # Verify the user can authenticate
                from django.contrib.auth import authenticate
                test_auth = authenticate(username='admin', password='ForceReset2025!')
                
                if test_auth:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Admin user created and verified successfully!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Username: admin')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Password: ForceReset2025!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Login at: /admin/')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Authentication test failed')
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
            raise e
