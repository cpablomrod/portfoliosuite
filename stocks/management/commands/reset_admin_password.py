from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Reset admin password to a known value'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to reset password for (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='NewAdmin2025!',
            help='New password (default: NewAdmin2025!)',
        )

    def handle(self, *args, **options):
        username = options['username']
        new_password = options['password']
        
        try:
            # Find the user
            user = User.objects.get(username=username)
            
            # Reset password and ensure all permissions are correct
            user.set_password(new_password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Password reset successfully for user: {username}')
            )
            
            # Verify permissions
            user.refresh_from_db()
            self.stdout.write('\n📊 User Status:')
            self.stdout.write(f'   - Username: {user.username}')
            self.stdout.write(f'   - Email: {user.email}')
            self.stdout.write(f'   - Is Active: {user.is_active}')
            self.stdout.write(f'   - Is Staff: {user.is_staff}')
            self.stdout.write(f'   - Is Superuser: {user.is_superuser}')
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 New admin login credentials:')
            )
            self.stdout.write(f'   Username: {username}')
            self.stdout.write(f'   Password: {new_password}')
            self.stdout.write('\n💡 You can now login to /admin/ with these credentials!')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User "{username}" does not exist')
            )
            
            # Offer to create the user
            self.stdout.write('\n🔧 Creating admin user...')
            try:
                user = User.objects.create_superuser(
                    username=username,
                    email='admin@portfoliosuite.com',
                    password=new_password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created new admin user: {username}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'🔑 Password: {new_password}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create admin user: {e}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error resetting password: {e}')
            )
