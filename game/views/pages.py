from django.views.generic import TemplateView


def get_players():
    from game.models import Player
    return Player.objects.order_by('joined_at')


class HomePageView(TemplateView):
    """
    Отображает страницу ожидания с списком игроков и QR-кодом
    """
    template_name = 'game/home.html'  # Путь к вашему новому шаблону

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем список активных игроков
        active_players = get_players()
        
        # Создаем список из 12 элементов (10 игроков + 2 пустых слота)
        players_list = list(active_players) + [None]*(12 - len(active_players))
        
        context.update({
            'players': players_list,
            'qr_code_url': 'images/qr.png'  # Путь к QR-коду
        })
        return context


class WaitingPageView(TemplateView):
    template_name = 'game/wait.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['players'] = get_players()
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
        context['players'] = get_players()
        return context
    
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

