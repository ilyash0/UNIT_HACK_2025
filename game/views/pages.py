from math import ceil

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView

from game.models import Prompt, Player


def get_players():
    from game.models import Player
    return Player.objects.order_by('joined_at')


class HomePageView(TemplateView):
    """
    Отображает страницу ожидания со списком игроков и QR-кодом
    """
    template_name = 'game/home.html'  # Путь к вашему новому шаблону

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        players = get_players()
        context['players'] = players
        return context


class WaitingPageView(TemplateView):
    template_name = 'game/wait.html'
    PROMPTS_FLAG_KEY = "prompts_assigned"
    PROMPTS_LOCK_KEY = "prompts_assign_lock"
    LOCK_TIMEOUT = 300

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.assign_prompts_once()
        context['players'] = get_players()
        return context

    def assign_prompts_once(self):
        if cache.get(self.PROMPTS_FLAG_KEY):
            return

        players = get_players()
        if len(players) < 4:
            return

        cache.set(self.PROMPTS_FLAG_KEY, True, None)
        num_prompts = ceil(len(players) / 2)
        prompts = list(Prompt.objects.order_by('?')[:num_prompts])

        with transaction.atomic():
            for i, player in enumerate(players):
                player.prompt = prompts[i // 2]
                player.save()

        channel_layer = get_channel_layer()
        for player in players:
            async_to_sync(channel_layer.group_send)(
                'bot',
                {
                    'type': 'receive_player_prompt',
                    'telegram_id': player.telegram_id,
                }
            )


class VotePageView(TemplateView):
    template_name = 'game/vote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cache.set("prompt_index", 1, timeout=300)
        players = Player.objects.all().order_by('prompt')
        context['prompt'] = players[0].prompt.phrase
        context['players'] = players
        return context


class WinPageView(TemplateView):
    template_name = 'game/win.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Player.objects.order_by('-vote_count')

        players = [
            {
                "username": player.username,
                "vote_count": player.vote_count or 0
            }
            for player in qs
        ]
        context['players'] = players
        return context

    def post(self, request, *args, **kwargs):
        Player.objects.all().delete()

        cache.clear()
        return redirect('game:home')
