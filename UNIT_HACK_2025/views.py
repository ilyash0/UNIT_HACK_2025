from django.views.generic import RedirectView


class HomeView(RedirectView):
    url = "game/"
