#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_base.settings')

    # =================================================================
    # FORCE SETTINGS (Bypassing the missing .env file)
    # =================================================================
    # We are injecting these directly into Python's environment so 
    # the settings.py file can find them without needing a separate file.
    
    os.environ['SECRET_KEY'] = 'django-insecure-kite-project-key-998877'
    os.environ['DEBUG'] = 'True'
    os.environ['ALLOWED_HOSTS'] = '127.0.0.1,localhost'
    
    # Email Settings
    os.environ['EMAIL_HOST_USER'] = 'rahulgupta002076@gmail.com'
    os.environ['EMAIL_HOST_PASSWORD'] = 'srouacpzorkwhgys'
    os.environ['EMAIL_HOST'] = 'smtp.gmail.com'
    os.environ['EMAIL_PORT'] = '587'
    os.environ['EMAIL_USE_TLS'] = 'True'
    # =================================================================

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()