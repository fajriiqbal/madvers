#!/usr/bin/env python
"""
Script to set up the Django database for the MTS website project.
Run this script to create all necessary database tables.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mts_website.settings')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line

def main():
    print("Setting up Django database for MTS Website...")
    print("=" * 50)
    
    try:
        # Run migrations
        print("1. Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("   ✓ Migrations completed successfully")
        
        # Create superuser if requested
        print("\n2. Creating superuser...")
        print("   Please provide the following information:")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = input("   Username (default: admin): ") or "admin"
        email = input("   Email (optional): ") or ""
        password = input("   Password: ")
        password_confirm = input("   Confirm password: ")
        
        if password != password_confirm:
            print("   ✗ Passwords don't match. Skipping superuser creation.")
            return
        
        if User.objects.filter(username=username).exists():
            print(f"   ✓ Superuser '{username}' already exists")
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"   ✓ Superuser '{username}' created successfully")
        
        print("\n" + "=" * 50)
        print("Database setup completed!")
        print(f"Admin URL: http://127.0.0.1:8000/admin/")
        print(f"Bendahara URL: http://127.0.0.1:8000/bendahara/login/")
        print(f"Username: {username}")
        print("Password: [your password]")
        print("\nTo start the server, run: python manage.py runserver")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\nIf you see database-related errors, try:")
        print("1. python manage.py migrate --run-syncdb")
        print("2. python manage.py makemigrations")
        print("3. python manage.py migrate")

if __name__ == '__main__':
    main()