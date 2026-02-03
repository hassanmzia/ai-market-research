import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create a default admin user if no admin exists.'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists. Skipping.'))
            return

        email = os.environ.get('ADMIN_EMAIL', 'admin@aimarketresearch.com')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123456')
        username = os.environ.get('ADMIN_USERNAME', 'admin')

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f'Default admin user created: {user.email}'))
