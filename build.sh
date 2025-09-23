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

# Also try our custom admin creation command
echo "Attempting to create admin with custom command..."
python manage.py create_admin || echo "Custom admin creation failed or already exists"

# Also try the alternative superuser creation command
echo "Attempting superuser creation with alternative command..."
python manage.py create_superuser_if_none_exists || echo "Alternative superuser creation failed or already exists"

# Show final status
echo "Checking for existing superusers..."
python -c "from django.contrib.auth.models import User; print(f'Superusers found: {list(User.objects.filter(is_superuser=True).values_list(\"username\", flat=True))}')" || echo "Could not check superusers"

echo "Build completed successfully!"
