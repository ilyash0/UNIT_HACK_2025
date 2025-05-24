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
from django.urls import path, re_path

from .consumers import PlayerConsumer, BotConsumer
from .views.API import PlayerConnectAPIView, PlayerAnswerAPIView, VoteAPIView, PromptAPIView, PlayerCountAPIView
from .views.pages import HomePageView
from .views.pages import WaitingPageView
from .views.pages import VotePageView
from .views.pages import WinPageView

app_name = 'game'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('api/connect/', PlayerConnectAPIView.as_view()),
    path('api/answer/', PlayerAnswerAPIView.as_view()),
    path('api/vote/', VoteAPIView.as_view()),
    path('api/prompt/', PromptAPIView.as_view()),
    path('api/count/', PlayerCountAPIView.as_view()),
    path('waiting/', WaitingPageView.as_view(), name='waiting'),
    path('vote/', VotePageView.as_view(), name='vote'),
    path('win/', WinPageView.as_view(), name='win'),
]

websocket_urlpatterns = [
    re_path(r'ws/players/$', PlayerConsumer.as_asgi()),
    re_path(r'ws/bot/$', BotConsumer.as_asgi()),
]
