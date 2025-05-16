from django.shortcuts import render
from django.views.generic import TemplateView


class MainMenuView(TemplateView):
    template_name = "game/main_menu.html"
