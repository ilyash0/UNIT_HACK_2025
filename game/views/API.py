from json import loads
from time import time, sleep

from django.core.cache import cache
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..models import Player


@method_decorator(csrf_exempt, name='dispatch')
class PlayerConnectAPIView(View):
    """
    API для подключения (регистрации) игрока.
    Ожидает POST-запрос с данными JSON: { '
        telegram_id': int,
        'username': str
    }
    В ответ всегда отправляет "OK" или 400 при ошибке.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            tg_id = data['telegram_id']
            username = data.get('username', '')
        except (ValueError, KeyError):
            return HttpResponseBadRequest('Invalid data')

        player, created = Player.objects.get_or_create(
            telegram_id=tg_id, username=username
        )
        if not created:
            player.username = username
            player.joined_at = timezone.now()
            player.save()

        return HttpResponse(status=204)

    def get(self, request, *args, **kwargs):
        players = Player.objects.order_by('joined_at')
        data = [
            {
                'id': p.id,
                'telegram_id': p.telegram_id,
                'username': p.username,
            }
            for p in players
        ]
        return JsonResponse({'players': data})


@method_decorator(csrf_exempt, name='dispatch')
class PlayerAnswerAPIView(View):
    CACHE_TIMEOUT = 5 * 60

    def post(self, request, *args, **kwargs):
        """
            API для приёма ответов пользователей и их кэширования.
            Ожидает POST с JSON: {
                "telegram_id": int>
                "answer": "<str>"
            }
            В ответ всегда отправляет 202 или 400 при ошибке.
        """
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            user_id = data['user_id']
            answer = data['answer']
        except (ValueError, KeyError):
            return HttpResponseBadRequest('Invalid JSON payload')

        player = Player.objects.get(telegram_id=user_id)
        player.answer = answer
        player.save()

        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
class VoteAPIView(View):
    CACHE_TIMEOUT = 60

    def post(self, request, *args, **kwargs):
        """
            API для голосования за лучший ответ.
            Ожидает POST с JSON: {
                "voter_id": int,         # идентификатор голосующего
                "candidate_id": int      # идентификатор того, за кого голосуют
            }
            В ответ всегда отправляет "OK" или 400 при ошибке.
        """
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            voter_id = int(data['voter_id'])
            candidate_id = int(data['candidate_id'])
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid JSON payload')

        player = Player.objects.get(telegram_id=voter_id)
        player.vote_telegram_id = candidate_id
        player.save()

        return HttpResponse(status=204)


class PromptAPIView(View):
    timeout = 10 * 60
    interval = 5

    def get(self, request, *args, **kwargs):
        """
            GET /api/get_prompt/?user_id=<ID>
            На вход принимает user_id: int
            В ответ отправляет JSON: {
                "user_id": int,         # идентификатор пользователя
                "prompt": str      # фраза
            }
        """
        user_id = request.GET.get('user_id')
        start_time = time()

        while time() - start_time < self.timeout:
            player = Player.objects.get(telegram_id=user_id)
            if player.prompt is not None:
                return JsonResponse({
                    'user_id': user_id,
                    'prompt': player.prompt
                })

            sleep(self.interval)

        return HttpResponse(status=408)
