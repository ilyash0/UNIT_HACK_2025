"""
WSGI config for UNIT_HACK_2025 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UNIT_HACK_2025.settings')
django.setup()

application = get_wsgi_application()
