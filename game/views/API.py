# from json import loads
#
# from django.http import JsonResponse, HttpResponseBadRequest
# from django.utils import timezone
# from django.views import View
#
# from ..models import Player
#
#
# class PlayerConnectAPIView(View):
#     """
#     API для подключения (регистрации) игрока.
#     Ожидает POST-запрос с данными JSON: { 'telegram_id': int, 'username': str }
#     """
#
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.json if hasattr(request, 'json') else loads(request.body)
#             tg_id = data['telegram_id']
#             username = data.get('username', '')
#         except (ValueError, KeyError):
#             return HttpResponseBadRequest('Invalid data')
#
#         player, created = Player.objects.get_or_create(
#             telegram_id=tg_id,
#             defaults={'username': username}
#         )
#         if not created:
#             player.username = username
#             player.joined_at = timezone.now()
#             player.save()
#
#         return JsonResponse({
#             'id': player.id,
#             'telegram_id': player.telegram_id,
#             'username': player.username,
#             'joined_at': player.joined_at.isoformat(),
#             'created': created,
#         })
#
#     def get(self, request, *args, **kwargs):
#         players = Player.objects.order_by('joined_at')
#         data = [
#             {
#                 'id': p.id,
#                 'telegram_id': p.telegram_id,
#                 'username': p.username,
#                 'joined_at': p.joined_at.isoformat(),
#             }
#             for p in players
#         ]
#         return JsonResponse({'players': data})
