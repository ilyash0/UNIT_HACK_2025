from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponseBadRequest
from game.models import Game, Player
from random import choices
from string import ascii_uppercase, digits

def generate_game_code(length=5):
    return ''.join(choices(ascii_uppercase + digits, k=length))

class MainMenuView(TemplateView):
    template_name = "game/main_menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['nickname'] = self.request.COOKIES.get('nickname', '')
        return ctx

def generate_game_code(length=5):
    return ''.join(choices(ascii_uppercase + digits, k=length))

class CreateGameView(View):
    template_name = "game/create_game.html"

    def get(self, request):
        nickname = request.COOKIES.get('nickname', '').strip()
        if not nickname:
            return redirect('game:main_menu')  # Или на страницу ввода никнейма
        return render(request, self.template_name, {'nickname': nickname})

    def post(self, request):
        nickname = request.COOKIES.get('nickname', '').strip()
        if not nickname:
            return HttpResponseBadRequest("Необходимо указать ваш никнейм")

        code = generate_game_code()
        while Game.objects.filter(code=code).exists():
            code = generate_game_code()

        game = Game.objects.create(code=code)
        Player.objects.create(game=game, nickname=nickname, is_host=True)

        response = redirect('game:lobby', code=game.code)
        response.set_cookie('game_code', game.code, max_age=7 * 24 * 3600)
        return response

class JoinGameView(View):
    template_name = "game/join_game.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        code = request.POST.get('code', '').strip().upper()
        nickname = request.COOKIES.get('nickname', '').strip()
        if not code or not nickname:
            return HttpResponseBadRequest("Необходимо указать код игры и ваш никнейм")

        game = get_object_or_404(Game, code=code)
        player_exists = Player.objects.filter(game=game, nickname=nickname).exists()
        if game.started and not player_exists:
            return HttpResponseBadRequest("Игра уже началась")

        Player.objects.get_or_create(game=game, nickname=nickname)

        response = redirect('game:lobby', code=game.code)
        response.set_cookie('game_code', game.code, max_age=7 * 24 * 3600)
        return response