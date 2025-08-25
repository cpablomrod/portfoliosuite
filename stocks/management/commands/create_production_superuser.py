from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Create a superuser for production deployment'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Username for the superuser')
        parser.add_argument('--email', default='admin@portfoliosuite.com', help='Email for the superuser')
        parser.add_argument('--password', help='Password for the superuser')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options.get('password')

        # Use environment variable for password if not provided
        if not password:
            password = os.environ.get('ADMIN_PASSWORD', 'admin123')

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            # Update the existing user to be superuser
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated {username} to superuser with new password')
            )
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser {username}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Superuser credentials:\n'
                f'Username: {username}\n'
                f'Email: {email}\n'
                f'Password: {"*" * len(password)}\n'
                f'Admin URL: /admin/'
            )
        )
