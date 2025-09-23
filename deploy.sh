#!/bin/bash

# Railway Deployment Script for Django Paystack Payment System
echo "🚀 Starting Railway deployment..."

# Show environment info
echo "📋 Environment check:"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "DEBUG: $DEBUG"
echo "ALLOWED_HOSTS: $ALLOWED_HOSTS"
echo "DATABASE_URL: ${DATABASE_URL:0:20}..." # Show first 20 chars only
echo "PAYSTACK_SECRET_KEY: ${PAYSTACK_SECRET_KEY:0:10}..." # Show first 10 chars only

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Try to install psycopg2-binary if not already installed
echo "🔧 Ensuring PostgreSQL adapter is available..."
pip install psycopg2-binary==2.9.7 --upgrade

# Django system check
echo "🔍 Running Django system check..."
python manage.py check --deploy

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Test database connection
echo "🔗 Testing database connection..."
python -c "import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('Database connection successful')"

# Show current database info
echo "📊 Database info:"
python -c "import django; django.setup(); from django.conf import settings; print(f'Engine: {settings.DATABASES[\"default\"][\"ENGINE\"]}'); print(f'Name: {settings.DATABASES[\"default\"][\"NAME\"]}');"

# Check for existing migrations
echo "🗺 Checking existing migrations..."
python manage.py showmigrations

# Make new migrations if needed
echo "🔄 Making new migrations..."
python manage.py makemigrations

# Run migrations with error handling
echo "🗄️ Running database migrations..."
python manage.py migrate --run-syncdb

# Create superuser if none exists
echo "👤 Creating superuser..."
python manage.py create_superuser_if_none_exists

# Test that Django can start (basic import test)
echo "🧪 Testing Django startup..."
python -c "import django; django.setup(); from django.conf import settings; print('Django settings loaded successfully')"

echo "✅ Deployment completed successfully!"
