"""
URL configuration for UNIT_HACK_2025 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from game.views import MainMenuView, CreateGameView, JoinGameView, LobbyView, ToggleReadyView

app_name = 'game'

urlpatterns = [
    path('game/', MainMenuView.as_view(), name='main_menu'),
    path('create/', CreateGameView.as_view(), name='create_game'),
    path('join/', JoinGameView.as_view(), name='join_game'),
    path('lobby/<str:code>/', LobbyView.as_view(), name='lobby'),
    path('lobby/<str:code>/ready/', ToggleReadyView.as_view(), name='toggle_ready'),
]
