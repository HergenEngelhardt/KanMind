#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.urls import get_resolver
from django.conf import settings

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
def show_urls():
    """Print all registered URLs to console."""
    print("\n=== REGISTERED URLS ===\n")
    
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    django.setup()
    
    resolver = get_resolver()
    
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            for p in pattern.url_patterns:
                print(f"{p.pattern} -> {p.callback}")
        else:
            print(f"{pattern.pattern} -> {pattern.callback}")

if __name__ == '__main__':
    show_urls()