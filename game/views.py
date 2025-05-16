from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class MainMenuView(TemplateView):
    template_name = "game/main_menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['nickname'] = self.request.COOKIES.get('nickname', '')
        return ctx
