from json import loads

from django.core.cache import cache
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..models import Player


class PlayerConnectAPIView(View):
    """
    API для подключения (регистрации) игрока.
    Ожидает POST-запрос с данными JSON: { '
        telegram_id': int,
        'username': str
    }
    В ответ всегда отправляет "OK" или 400 при ошибке.
    """

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            tg_id = data['telegram_id']
            username = data.get('username', '')
        except (ValueError, KeyError):
            return HttpResponseBadRequest('Invalid data')

        player, created = Player.objects.get_or_create(
            telegram_id=tg_id,
            defaults={'username': username}
        )
        if not created:
            player.username = username
            player.joined_at = timezone.now()
            player.save()

        return HttpResponse(status=204)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        players = Player.objects.order_by('joined_at')
        data = [
            {
                'id': p.id,
                'telegram_id': p.telegram_id,
                'username': p.username,
                'joined_at': p.joined_at.isoformat(),
            }
            for p in players
        ]
        return JsonResponse({'players': data})


class PlayerAnswerAPIView(View):
    """
    API для приёма ответов пользователей и их кэширования.
    Ожидает POST с JSON: {
        "telegram_id": int>
        "question_id": int,   # необязательное поле — идентификатор/текст вопроса
        "answer": "<str>"
    }
    В ответ всегда отправляет 202 или 400 при ошибке.
    """

    CACHE_TIMEOUT = 5 * 60

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            user_id = data['user_id']
            answer = data['answer']
            question_id = data.get('question_id', '1')
        except (ValueError, KeyError):
            return HttpResponseBadRequest('Invalid JSON payload')

        cache_key = f"user_{user_id}_answer_{question_id}"

        cache.set(cache_key, answer, timeout=self.CACHE_TIMEOUT)

        return HttpResponse(status=204)


class VoteAPIView(View):
    """
    API для голосования за лучший ответ.
    Ожидает POST с JSON: {
        "voter_id": int,         # идентификатор голосующего
        "candidate_id": int      # идентификатор того, за кого голосуют
    }
    В ответ всегда отправляет "OK" или 400 при ошибке.
    """

    CACHE_TIMEOUT = 60

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = request.json if hasattr(request, 'json') else loads(request.body)
            voter_id = int(data['voter_id'])
            candidate_id = int(data['candidate_id'])
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid JSON payload')

        voter_key = f"vote_voter_{voter_id}"
        if cache.get(voter_key) is not None:
            return HttpResponseBadRequest('User has already voted')

        cache.set(voter_key, candidate_id, timeout=self.CACHE_TIMEOUT)

        candidate_key = f"vote_count_{candidate_id}"
        current = cache.get(candidate_key, 0)
        cache.set(candidate_key, current + 1, timeout=self.CACHE_TIMEOUT)

        return HttpResponse(status=204)
