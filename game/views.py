from random import choices
from string import ascii_uppercase, digits

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponseBadRequest
from django.views.generic import TemplateView

from game.models import Game


def generate_game_code(length=5):
    return ''.join(choices(ascii_uppercase + digits, k=length))


class MainMenuView(TemplateView):
    template_name = "game/main_menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['nickname'] = self.request.COOKIES.get('nickname', '')
        return ctx


class CreateGameView(View):
    template_name = "game/create_game.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        nickname = request.POST.get('nickname', '').strip()
        if not nickname:
            return HttpResponseBadRequest("Необходимо указать имя игры и ваш никнейм")

        code = generate_game_code()
        while Game.objects.filter(code=code).exists():
            code = generate_game_code()

        Game.objects.create(code=code)

        response = redirect('game')
        response.set_cookie('nickname', nickname, max_age=7 * 24 * 3600)
        response.set_cookie('game_code', code, max_age=7 * 24 * 3600)
        return response


class JoinGameView(View):
    template_name = "game/join_game.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        code = request.POST.get('code', '').strip().upper()
        nickname = request.POST.get('nickname', '').strip()
        if not code or not nickname:
            return HttpResponseBadRequest("Необходимо указать код игры и ваш никнейм")

        game = get_object_or_404(Game, code=code)

        response = redirect('game')
        response.set_cookie('nickname', nickname, max_age=7 * 24 * 3600)
        response.set_cookie('game_code', game.code, max_age=7 * 24 * 3600)
        return response
