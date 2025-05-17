from django.views.generic import TemplateView


def get_players():
    from game.models import Player
    return Player.objects.order_by('joined_at')


class HomePageView(TemplateView):
    """
    Отображает главную страницу с визуалом и списком всех присоединившихся игроков.
    """
    template_name = 'game/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['players'] = get_players()
        return context
