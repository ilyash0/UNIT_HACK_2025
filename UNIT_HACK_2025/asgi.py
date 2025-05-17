"""
ASGI config for UNIT_HACK_2025 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import game.urls

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UNIT_HACK_2025.settings')
django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            game.urls.websocket_urlpatterns
        )
    ),
})
