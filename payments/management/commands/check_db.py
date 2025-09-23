from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management.color import make_style
import sys


class Command(BaseCommand):
    help = 'Test database connection and display configuration'
    
    def __init__(self):
        super().__init__()
        self.style = make_style()

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed database configuration',
        )

    def handle(self, *args, **options):
        try:
            # Test database connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                self.stdout.write(
                    self.style.SUCCESS('✅ Database connection successful!')
                )
            
            # Display database configuration
            db_config = connection.settings_dict
            self.stdout.write("\n📊 Database Configuration:")
            self.stdout.write(f"  Engine: {db_config['ENGINE']}")
            self.stdout.write(f"  Name: {db_config['NAME']}")
            
            if 'HOST' in db_config and db_config['HOST']:
                self.stdout.write(f"  Host: {db_config['HOST']}")
                self.stdout.write(f"  Port: {db_config['PORT']}")
                self.stdout.write(f"  User: {db_config['USER']}")
            
            if options['verbose']:
                self.stdout.write(f"\n🔧 Full Configuration:")
                for key, value in db_config.items():
                    if key == 'PASSWORD':
                        self.stdout.write(f"  {key}: {'*' * len(str(value))}")
                    else:
                        self.stdout.write(f"  {key}: {value}")
            
            # Test database version
            if 'postgresql' in db_config['ENGINE']:
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0]
                self.stdout.write(f"\n🐘 PostgreSQL Version: {db_version.split(',')[0]}")
            elif 'sqlite' in db_config['ENGINE']:
                cursor.execute("SELECT sqlite_version()")
                db_version = cursor.fetchone()[0]
                self.stdout.write(f"\n📱 SQLite Version: {db_version}")
            else:
                try:
                    cursor.execute("SELECT version()")
                    db_version = cursor.fetchone()[0]
                    self.stdout.write(f"\n💾 Database Version: {db_version}")
                except:
                    self.stdout.write(f"\n💾 Database: {db_config['ENGINE'].split('.')[-1].title()}")
            
            # Check if tables exist
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """ if 'postgresql' in db_config['ENGINE'] else """
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table'
            """)
            
            table_count = cursor.fetchone()[0]
            self.stdout.write(f"\n📋 Database Tables: {table_count}")
            
            cursor.close()
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Database is ready for use!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {str(e)}')
            )
            
            # Provide helpful suggestions
            db_config = connection.settings_dict
            if 'postgresql' in db_config['ENGINE']:
                self.stdout.write("\n💡 PostgreSQL Connection Tips:")
                self.stdout.write("  1. Make sure PostgreSQL is running")
                self.stdout.write("  2. Check your DATABASE_URL or database credentials")
                self.stdout.write("  3. Verify the database exists")
                self.stdout.write("  4. For Docker: run 'docker-compose up -d postgres'")
                self.stdout.write("  5. For Windows: check PostgreSQL service in Services panel")
            
            sys.exit(1)