#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Fix SSL certificate verification BEFORE any Django/network imports.
# This must be the very first thing executed.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sys_services.ssl_fix import apply_ssl_fix
apply_ssl_fix()

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')
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
