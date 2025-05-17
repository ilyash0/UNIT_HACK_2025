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
            telegram_id=tg_id,
            defaults={'username': username}
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
                'joined_at': p.joined_at.isoformat(),
            }
            for p in players
        ]
        return JsonResponse({'players': data})


@method_decorator(csrf_exempt, name='dispatch')
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

    def get(self, request, *args, **kwargs):
        """
           В ответ отправляет JSON: [
                {
                    "user_id": int,    # идентификатор пользователя
                    "answer": str      # ответ
                },
                {
                    "user_id": int,    # идентификатор пользователя
                    "answer": str      # ответ
                }
           ]
        """
        prompt_index = cache.get("prompt_index")

        matches = []
        players = Player.objects.order_by('prompt')[prompt_index - 1:2 * prompt_index]
        for p in players:
            matches.append({
                'user_id': p.id,
                'answer': p.answer
            })

        return JsonResponse(matches, status=204)


@method_decorator(csrf_exempt, name='dispatch')
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


class PromptAPIView(View):
    """
    GET /api/get_prompt/?user_id=<ID>
    На вход принимает user_id: int
    В ответ отправляет JSON: {
        "user_id": int,         # идентификатор пользователя
        "prompt": str      # фраза
    }
    """
    timeout = 10 * 60
    interval = 5

    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')
        start_time = time()
        question_id = 0
        prompt_key = f"user_{user_id}_answer_{question_id}"

        while time() - start_time < self.timeout:
            prompt = cache.get(prompt_key)
            if prompt is not None:
                return JsonResponse({
                    'user_id': user_id,
                    'prompt': prompt
                })

            sleep(self.interval)

        return HttpResponse(status=408)
