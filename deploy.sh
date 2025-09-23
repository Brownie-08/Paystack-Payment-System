#!/bin/bash

# Railway Deployment Script for Django Paystack Payment System
echo "🚀 Starting Railway deployment..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Try to install psycopg2-binary if not already installed
echo "🔧 Ensuring PostgreSQL adapter is available..."
pip install psycopg2-binary==2.9.7 --upgrade

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations with error handling
echo "🗄️ Running database migrations..."
python manage.py migrate --run-syncdb

# Create superuser if none exists
echo "👤 Creating superuser..."
python manage.py create_superuser_if_none_exists

echo "✅ Deployment completed successfully!"