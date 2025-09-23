#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Create admin user for production
echo "Creating admin user..."
# Try multiple methods to create admin user
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Using Django's built-in createsuperuser with DJANGO_SUPERUSER_* variables"
    python manage.py createsuperuser --noinput || echo "Django createsuperuser failed or already exists"
fi

# Try the comprehensive superuser creation command (this handles null bytes better)
echo "Attempting superuser creation with alternative command..."
python manage.py create_superuser_if_none_exists || echo "Alternative superuser creation failed or already exists"

# Show final status with proper Django setup
echo "Checking for existing superusers..."
python manage.py shell -c "from django.contrib.auth.models import User; users = list(User.objects.filter(is_superuser=True).values_list('username', flat=True)); print(f'Superusers found: {users}')" || echo "Could not check superusers, but deployment continues"

echo "Build completed successfully!"
