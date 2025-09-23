"""
Django management command to create a superuser automatically from environment variables.

This command will create a superuser if none exists, using the following environment variables:
- ADMIN_USERNAME (default: 'admin')
- ADMIN_EMAIL (default: 'admin@example.com') 
- ADMIN_PASSWORD (default: 'admin123')

Usage:
    python manage.py create_superuser_if_none_exists

This is particularly useful for automated deployments where you need to ensure
an admin user exists without manual intervention.
"""

import os
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a superuser if none exists (for automated deployments)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Admin username (defaults to ADMIN_USERNAME env var or "admin")',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Admin email (defaults to ADMIN_EMAIL env var or "admin@example.com")',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password (defaults to ADMIN_PASSWORD env var or "admin123")',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Create superuser even if others exist',
        )

    def handle(self, *args, **options):
        """Create superuser if none exists or if force flag is used."""
        
        # Get credentials from command line args, environment variables, or defaults
        username = (
            options.get('username') or
            os.environ.get('ADMIN_USERNAME', 'admin')
        )
        email = (
            options.get('email') or
            os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        )
        password = (
            options.get('password') or
            os.environ.get('ADMIN_PASSWORD', 'admin123')
        )

        # Check if superuser already exists
        if not options.get('force') and User.objects.filter(is_superuser=True).exists():
            existing_superusers = User.objects.filter(is_superuser=True).values_list('username', flat=True)
            self.stdout.write(
                self.style.WARNING(
                    f'Superuser(s) already exist: {", ".join(existing_superusers)}. '
                    'Use --force to create anyway.'
                )
            )
            logger.info(f'Superuser creation skipped - existing superusers: {", ".join(existing_superusers)}')
            return

        # Check if user with this username already exists
        if User.objects.filter(username=username).exists():
            if options.get('force'):
                self.stdout.write(
                    self.style.WARNING(f'User "{username}" already exists, skipping creation.')
                )
                logger.warning(f'User "{username}" already exists, skipped creation')
                return
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'User "{username}" already exists. Use a different username or --force flag.'
                    )
                )
                logger.error(f'User "{username}" already exists, creation failed')
                return

        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            # Success message
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Superuser created successfully!\n'
                    f'   Username: {username}\n'
                    f'   Email: {email}\n'
                    f'   You can now log in to /admin/ with these credentials.'
                )
            )
            
            logger.info(f'Superuser created successfully: {username} ({email})')
            
            # Create user profile if it doesn't exist
            try:
                from payments.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ User profile created for {username}')
                    )
                    logger.info(f'User profile created for superuser: {username}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  Could not create user profile: {e}')
                )
                logger.warning(f'Could not create user profile for {username}: {e}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating superuser: {e}')
            )
            logger.error(f'Error creating superuser: {e}')
            raise

    def get_version(self):
        return '1.0.0'