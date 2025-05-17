from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from game.models import Game, Player


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
