import logging
from asyncio import sleep
from json import loads, JSONDecodeError
from math import ceil
from time import time

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from ..models import Player


@method_decorator(csrf_exempt, name='dispatch')
class PlayerConnectAPIView(View):
    """
    API для подключения (регистрации) игрока.
    Ожидает POST-запрос с данными JSON: {
        'telegram_id': int,
        'username': str
    }
    В ответ всегда отправляет "OK" или 400 при ошибке.
    """

    def post(self, request, *args, **kwargs):
        try:
            if request.content_type == 'application/json':
                data = loads(request.body)
            else:
                data = request.POST

            tg_id = data['telegram_id']
            username = data.get('username', '')
        except JSONDecodeError:
            logging.error("JSONDecodeError: malformed JSON")
            return HttpResponseBadRequest("Malformed JSON payload")
        except (ValueError, KeyError):
            logging.log(1, 'Invalid data')
            return HttpResponseBadRequest('Invalid data')

        try:
            with transaction.atomic():
                player, created = Player.objects.get_or_create(
                    telegram_id=tg_id,
                    defaults={'username': username, 'prompt': None, 'answer': None, 'vote_count': None},
                )
        except IntegrityError:
            player = Player.objects.get(telegram_id=tg_id)
            created = False

        if not created:
            player.username = username
            player.joined_at = timezone.now()
            player.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'players',
            {
                'type': 'player_joined',
                'player': {
                    'id': player.id,
                    'username': player.username,
                },
            }
        )

        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
class PlayerAnswerAPIView(View):
    CACHE_TIMEOUT = 5 * 60
    TIMEOUT = 10 * 60
    interval = 15

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
            if request.content_type == 'application/json':
                data = loads(request.body)
            else:
                data = request.POST

            user_id = data['telegram_id']
            answer = data['answer']
        except (ValueError, KeyError):
            return HttpResponseBadRequest('Invalid JSON payload')

        player = Player.objects.get(telegram_id=user_id)
        player.answer = answer
        player.save()

        total_players = Player.objects.count()
        answered_players = Player.objects.filter(answer__isnull=False).count()

        if answered_players >= total_players > 0:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'players',
                {
                    'type': 'all_answers_received',
                }
            )

        return HttpResponse(status=204)

    def get(self, request, *args, **kwargs):
        """
           В ответ отправляет JSON: {
                "prompt": str,
                "answer0":
                    {
                        "telegram_id": int,    # идентификатор пользователя
                        "answer": str          # ответ
                    },
                "answer1":
                    {
                        "telegram_id": int,    # идентификатор пользователя
                        "answer": str          # ответ
                    }
           }
        """
        prompt_index = cache.get("prompt_index", None)
        start_time = time()

        while time() - start_time < self.TIMEOUT:
            if prompt_index is None:
                sleep(self.interval)
                prompt_index = cache.get("prompt_index", None)
            else:
                break

        if prompt_index is None:
            return JsonResponse(
                {"error": "No prompt_index found in cache within TIMEOUT."},
                status=408
            )

        players = Player.objects.all().order_by('prompt')[2 * (prompt_index - 1):2 * prompt_index]

        result = {
            "prompt": players[0].prompt.phrase,
            "answer0": {
                "telegram_id": players[0].telegram_id,
                "answer": players[0].answer,
            },
            "answer1": {
                "telegram_id": players[1].telegram_id,
                "answer": players[1].answer,
            },
        }

        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class VoteAPIView(View):
    CACHE_TIMEOUT = 60

    def post(self, request, *args, **kwargs):
        try:
            if request.content_type == 'application/json':
                data = loads(request.body)
            else:
                data = request.POST

            voter_id = int(data['voter_id'])
            candidate_id = int(data['candidate_id'])
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid JSON payload')

        prompt_index = cache.get("prompt_index")
        voter = Player.objects.get(telegram_id=voter_id)
        if voter.is_voted:
            return HttpResponseBadRequest('Already voted')

        voter.is_voted = True
        voter.save()  # Сохраняем изменения

        candidate = Player.objects.get(telegram_id=candidate_id)
        candidate.vote_count = 0 if candidate.is_voted is None else candidate.is_voted
        candidate.vote_count += 1
        candidate.save()

        # Проверяем, все ли игроки проголосовали
        if not Player.objects.filter(is_voted=False).exists():
            for p in Player.objects.filter(is_voted=True):
                p.is_voted = False

            players = Player.objects.all().order_by('prompt')[prompt_index - 1:2 * prompt_index]
            cache.set("prompt_index", prompt_index + 1, timeout=300)

            result = {
                'all_voted': prompt_index == ceil(Player.objects.count() / 2),
                "prompt": players[0].prompt.phrase,
                "player0": {
                    "username": players[0].username,
                    "answer": players[0].answer,
                    'vote_count': players[0].vote_count or 0,
                },
                "player1": {
                    "username": players[1].username,
                    "answer": players[1].answer,
                    'vote_count': players[1].vote_count or 0,
                },
            }

            # Отправляем сообщение через WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'players',
                {
                    'type': 'all_voted',
                    'message': result,
                }
            )

        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
class PromptAPIView(View):
    timeout = 10 * 60
    interval = 5

    async def get(self, request, *args, **kwargs):
        """
            GET /api/get_prompt/?telegram_id=<ID>
            На вход принимает user_id: int
            В ответ отправляет JSON: {
                "telegram_id": int,         # идентификатор пользователя
                "prompt": str      # фраза
            }
        """
        telegram_id = request.GET.get('telegram_id')
        start_time = time()

        while time() - start_time < self.timeout:
            player = await Player.objects.aget(telegram_id=telegram_id)
            prompt = await sync_to_async(lambda: player.prompt)()
            if prompt is not None:
                return JsonResponse({
                    'telegram_id': telegram_id,
                    'prompt': player.prompt.phrase
                })

            await sleep(self.interval)

        return HttpResponse(status=408)


@method_decorator(csrf_exempt, name='dispatch')
class PlayerCountAPIView(APIView):
    async def get(self, request, *args, **kwargs):
        count = await Player.objects.acount()
        prompt_index = await sync_to_async(cache.get)("prompt_index", 0)
        players_pairs_count = ceil(count / 2) - (prompt_index - 1)
        return JsonResponse({'count': players_pairs_count})
