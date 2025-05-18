from math import ceil

from django.core.cache import cache
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        players = get_players()

        first_time = cache.add("prompts_assigned", True)

        if first_time:
            if len(players) < 4:
                return redirect("game:home")

            num_prompts = ceil(len(players) / 2)
            prompts = Prompt.objects.order_by('?')[:num_prompts]

            for i, player in enumerate(players):
                player.prompt = prompts[i // 2]
                player.save()

        context['players'] = players
        return context


class VotePageView(TemplateView):
    template_name = 'game/vote.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['players'] = get_players()
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


"""
Вьюшку для win`а с чатом накидал
from django.views.generic import TemplateView
from .models import Player  # ваша модель игрока

class ResultsPageView(TemplateView):
    template_name = 'game/results.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Получаем всех игроков, сортируя по убыванию очков (votes, score и т.п.)
        players = Player.objects.order_by('-score')  
        if not players:
            ctx['results'] = []
            return ctx

        max_score = players[0].score

        # Формируем список c процентами ширины бара
        results = []
        for p in players:
            pct = (p.score / max_score) * 100  # процент от максимума
            results.append({
                'username': p.username,
                'score': p.score,
                'percentage': pct,
                'is_winner': p.score == max_score,
            })

        ctx['results'] = results
        return ctx

"""
