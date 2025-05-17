from django.views.generic import TemplateView


def get_players():
    from game.models import Player
    return Player.objects.order_by('joined_at')


class HomePageView(TemplateView):
    """
    Отображает главную страницу визуалом и списком всех присоединившихся игроков.
    """
    template_name = 'game/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['players'] = get_players()
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

