from django.views.generic import TemplateView

from game.models import Player


class HomePageView(TemplateView):
    """
    Отображает главную страницу с визуалом и списком всех присоединившихся игроков.
    """
    template_name = 'game/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['players'] = Player.objects.order_by('joined_at')
        return context
