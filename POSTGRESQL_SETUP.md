# PostgreSQL Setup Guide

This guide will help you set up PostgreSQL for your Django Payment App both locally and in production.

## Local Development Setup

### Option 1: Install PostgreSQL on Windows

1. **Download PostgreSQL**:
   - Go to https://www.postgresql.org/download/windows/
   - Download the latest version (15.x or 14.x recommended)
   - Run the installer

2. **Installation Configuration**:
   - Set a password for the `postgres` user (remember this!)
   - Port: 5432 (default)
   - Locale: Default locale

3. **Create Database**:
   ```sql
   -- Connect to PostgreSQL as postgres user
   psql -U postgres
   
   -- Create database for your payment app
   CREATE DATABASE payment_db;
   
   -- Create a user for your app (optional but recommended)
   CREATE USER payment_user WITH PASSWORD 'your_secure_password';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE payment_db TO payment_user;
   
   -- Exit
   \q
   ```

### Option 2: Use Docker (Recommended for Development)

1. **Install Docker Desktop** from https://www.docker.com/products/docker-desktop/

2. **Create docker-compose.yml** in your project root:
   ```yaml
   version: '3.8'
   
   services:
     postgres:
       image: postgres:15-alpine
       container_name: payment_postgres
       environment:
         POSTGRES_DB: payment_db
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: password
         POSTGRES_HOST_AUTH_METHOD: trust
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # Optional
   
   volumes:
     postgres_data:
   ```

3. **Start PostgreSQL**:
   ```bash
   docker-compose up -d postgres
   ```

4. **Connect to verify**:
   ```bash
   docker exec -it payment_postgres psql -U postgres -d payment_db
   ```

### Option 3: Use Cloud PostgreSQL (Development)

1. **Neon (Free PostgreSQL)**:
   - Sign up at https://neon.tech
   - Create a database
   - Copy the connection string

2. **Supabase (Free PostgreSQL)**:
   - Sign up at https://supabase.com
   - Create a project
   - Go to Settings > Database
   - Copy the connection string

## Environment Configuration

### For Local Development

1. **Create `.env` file** (copy from `.env.example`):
   ```env
   # Use DATABASE_URL for PostgreSQL
   DATABASE_URL=postgresql://postgres:password@localhost:5432/payment_db
   
   # Other settings
   DEBUG=True
   SECRET_KEY=your-local-secret-key
   PAYSTACK_SECRET_KEY=sk_test_your_test_key
   PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
   ```

2. **Alternative: Use individual database settings**:
   ```env
   USE_POSTGRESQL=True
   DB_NAME=payment_db
   DB_USER=postgres
   DB_PASSWORD=password
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Database Migration

### Initial Migration
```bash
# Make sure PostgreSQL is running
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Test the connection
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT version();")
>>> cursor.fetchone()
```

### Reset Database (if needed)
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS payment_db;"
psql -U postgres -c "CREATE DATABASE payment_db;"

# Re-run migrations
python manage.py migrate
```

## Production Setup (Render)

### Automatic Setup
When you deploy to Render using the `render.yaml` file:
1. Render automatically creates a PostgreSQL database
2. Sets the `DATABASE_URL` environment variable
3. Your Django app connects automatically

### Manual Verification
1. Check Render dashboard for database status
2. View database connection string in environment variables
3. Monitor database logs for connection issues

## Connection Testing

### Test Database Connection
```python
# In Django shell (python manage.py shell)
from django.db import connection
from django.core.management import execute_from_command_line

# Test connection
try:
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("✅ Database connection successful!")
    print(f"Database: {connection.settings_dict['NAME']}")
    print(f"Host: {connection.settings_dict['HOST']}")
    print(f"Engine: {connection.settings_dict['ENGINE']}")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### Test with Management Command
```bash
# Check database status
python manage.py dbshell --version

# Test migrations
python manage.py showmigrations
```

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   ```
   Error: connection to server at "localhost", port 5432 failed
   ```
   - **Solution**: Make sure PostgreSQL service is running
   - Windows: Check Services panel for PostgreSQL
   - Docker: Run `docker-compose up -d postgres`

2. **Authentication Failed**:
   ```
   Error: authentication failed for user "postgres"
   ```
   - **Solution**: Check username/password in your `.env` file
   - Verify PostgreSQL user exists with correct password

3. **Database Does Not Exist**:
   ```
   Error: database "payment_db" does not exist
   ```
   - **Solution**: Create the database manually
   ```sql
   psql -U postgres -c "CREATE DATABASE payment_db;"
   ```

4. **SSL Connection Error** (in production):
   ```
   Error: SSL connection has been closed unexpectedly
   ```
   - **Solution**: This is handled automatically in the updated settings.py

### Environment-Specific Issues

**Local Development**:
- Check if port 5432 is available
- Verify PostgreSQL is installed and running
- Test connection with `psql -U postgres`

**Production (Render)**:
- Verify database service is created and running
- Check environment variables in Render dashboard
- Review application logs for connection errors

## Database Management Tools

### Command Line Tools
- **psql**: Built-in PostgreSQL client
- **pgcli**: Enhanced PostgreSQL client with autocomplete

### GUI Tools
- **pgAdmin**: Full-featured PostgreSQL administration
- **DBeaver**: Universal database tool
- **DataGrip**: JetBrains database IDE

### Web-based Tools
- **Django Admin**: Built-in Django administration
- **Render Dashboard**: Database monitoring and management

## Performance Tips

### Local Development
- Use connection pooling (already configured in settings.py)
- Enable query logging in DEBUG mode
- Use database indexes for frequent queries

### Production
- Monitor database performance in Render dashboard
- Consider upgrading to paid database plans for better performance
- Implement database backups (Render provides automatic backups)

## Security Best Practices

1. **Never commit credentials to Git**
2. **Use strong passwords for database users**
3. **Enable SSL in production (automatically handled)**
4. **Regularly update PostgreSQL versions**
5. **Monitor database access logs**

---

## Quick Start Commands

```bash
# If using Docker
docker-compose up -d postgres

# If using local PostgreSQL
# (Make sure PostgreSQL service is running)

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Test database connection
python manage.py shell -c "from django.db import connection; print(connection.cursor().execute('SELECT 1'))"
```