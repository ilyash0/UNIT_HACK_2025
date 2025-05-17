from random import choices
from string import ascii_uppercase, digits

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponseBadRequest
from django.views.generic import TemplateView

from game.models import Game, Player


def generate_game_code(length=5):
    return ''.join(choices(ascii_uppercase + digits, k=length))


class MainMenuView(TemplateView):
    template_name = "game/main_menu.html"


class CreateGameView(View):
    template_name = "game/create_game.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        nickname = request.POST.get('nickname', '').strip()
        if not nickname:
            return HttpResponseBadRequest("Необходимо указать ваш никнейм")

        code = generate_game_code()
        while Game.objects.filter(code=code).exists():
            code = generate_game_code()

        game = Game.objects.create(code=code)
        Player.objects.create(game=game, nickname=nickname, is_host=True)

        response = redirect('game:lobby', code=game.code)
        response.set_cookie('nickname', nickname, max_age=7 * 24 * 3600)
        response.set_cookie('game_code', game.code, max_age=7 * 24 * 3600)
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
        if game.started:
            return HttpResponseBadRequest("Игра уже началась")

        Player.objects.get_or_create(game=game, nickname=nickname)

        response = redirect('game:lobby', code=game.code)
        response.set_cookie('nickname', nickname, max_age=7 * 24 * 3600)
        response.set_cookie('game_code', game.code, max_age=7 * 24 * 3600)
        return response


class LobbyView(TemplateView):
    template_name = "game/lobby.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        code = kwargs.get('code')
        game = get_object_or_404(Game, code=code)
        nickname = self.request.COOKIES.get('nickname', '')
        ctx['game'] = game
        ctx['players'] = game.players.order_by('joined_at')
        ctx['me'] = game.players.filter(nickname=nickname).first()
        return ctx


class ToggleReadyView(View):
    def post(self, request, code):
        nickname = request.COOKIES.get('nickname', '')
        game = get_object_or_404(Game, code=code)
        player = get_object_or_404(Player, game=game, nickname=nickname)

        player.ready = not player.ready
        player.save()

        if game.all_ready():
            game.started = True
            game.save()

        return redirect('game:lobby', code=code)
