from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix admin user permissions'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@portfoliosuite.com'
        password = 'admin123'
        
        try:
            # Get or create admin user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ CREATED superuser {username}')
                )
            else:
                # Force update permissions
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.email = email
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ UPDATED {username} with admin permissions')
                )
            
            # Verify permissions
            user.refresh_from_db()
            self.stdout.write(f'📊 User Status:')
            self.stdout.write(f'   - Username: {user.username}')
            self.stdout.write(f'   - Is Active: {user.is_active}')
            self.stdout.write(f'   - Is Staff: {user.is_staff}')
            self.stdout.write(f'   - Is Superuser: {user.is_superuser}')
            self.stdout.write(f'   - Can login to admin: {user.is_staff and user.is_active}')
            
            self.stdout.write('\n🎉 Admin login credentials:')
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Password: {password}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing admin user: {e}')
            )
