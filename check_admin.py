#!/usr/bin/env python
"""
Simple script to check admin users and optionally reset passwords.
Usage: python check_admin.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_project.settings')
django.setup()

from django.contrib.auth.models import User

def main():
    print("=== Admin User Status ===")
    
    # Get all superusers
    superusers = User.objects.filter(is_superuser=True)
    
    if not superusers.exists():
        print("❌ No admin/superusers found!")
        print("Run: python manage.py create_superuser_if_none_exists")
        return
    
    print(f"✅ Found {superusers.count()} admin user(s):")
    for user in superusers:
        print(f"   👤 Username: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🗓️  Created: {user.date_joined}")
        print(f"   🔄 Last Login: {user.last_login or 'Never'}")
        print()
    
    # Offer to reset password if needed
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        username = input("Enter username to reset password: ").strip()
        try:
            user = User.objects.get(username=username, is_superuser=True)
            new_password = input("Enter new password: ").strip()
            user.set_password(new_password)
            user.save()
            print(f"✅ Password updated for {username}")
        except User.DoesNotExist:
            print(f"❌ Admin user '{username}' not found")
        except Exception as e:
            print(f"❌ Error updating password: {e}")

if __name__ == "__main__":
    main()