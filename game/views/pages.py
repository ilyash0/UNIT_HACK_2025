from django.views.generic import TemplateView


class HomePageView(TemplateView):
    """
    Отображает главную страницу с визуалом и списком всех присоединившихся игроков.
    """
    template_name = 'game/home.html'
