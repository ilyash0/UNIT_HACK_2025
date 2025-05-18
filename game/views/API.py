import asyncio
import json
import math

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..models import Player


@database_sync_to_async
def create_or_update_player_record(tg_id: int, username: str) -> (Player, bool):
    """
    Atomically try to create a new Player with given telegram_id.
    If it already exists, fetch it and indicate created=False.
    """
    try:
        with transaction.atomic():
            player, created = Player.objects.get_or_create(
                telegram_id=tg_id,
                defaults={
                    'username': username,
                    'prompt': None,
                    'answer': None,
                    'vote_count': 0,
                    'is_voted': False,
                },
            )
    except IntegrityError:
        player = Player.objects.get(telegram_id=tg_id)
        created = False

    if not created:
        player.username = username
        player.joined_at = timezone.now()
        player.save()

    return player, created


@database_sync_to_async
def save_player_answer(user_id: int, answer_text: str):
    """
    Fetch the Player with telegram_id=user_id, update its answer and save.
    """
    player = Player.objects.get(telegram_id=user_id)
    player.answer = answer_text
    player.save()
    return None


@database_sync_to_async
def fetch_two_players_by_prompt(prompt_index: int):
    """
    Return exactly two Player instances ordered by `prompt`, starting
    at index (prompt_index - 1). Assumes that there are at least 2 players
    in that slice.
    """
    queryset = Player.objects.order_by('prompt')
    subset = list(queryset[prompt_index - 1: 2 * prompt_index])
    return subset


@database_sync_to_async
def get_player_by_telegram_id(tg_id: int):
    return Player.objects.get(telegram_id=tg_id)


@database_sync_to_async
def increment_candidate_vote(candidate_id: int):
    """
    Fetch Player with telegram_id=candidate_id, increment vote_count.
    """
    candidate = Player.objects.get(telegram_id=candidate_id)
    if candidate.vote_count is None:
        candidate.vote_count = 0
    candidate.vote_count += 1
    candidate.save()
    return None


@database_sync_to_async
def mark_player_voted(voter_id: int):
    """
    Fetch Player with telegram_id=voter_id, mark is_voted=True.
    """
    voter = Player.objects.get(telegram_id=voter_id)
    voter.is_voted = True
    voter.save()
    return None


@database_sync_to_async
def get_cached_prompt_index():
    """
    Wrapper around cache.get for "prompt_index".
    """
    return cache.get("prompt_index")


@database_sync_to_async
def get_player_count():
    """
    Return total Player count.
    """
    return Player.objects.count()


@method_decorator(csrf_exempt, name='dispatch')
class PlayerConnectAPIView(View):
    """
    Async API endpoint for registering (connecting) a player.
    Expects POST JSON: {
        "telegram_id": int,
        "username": str
    }
    Returns HTTP 204 on success or 400 on error.
    """

    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            tg_id = int(data['telegram_id'])
            username = data.get('username', '')
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid data')

        player, created = await create_or_update_player_record(tg_id, username)

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
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
    """
    Async API endpoint for receiving and retrieving player answers.
    """

    CACHE_TIMEOUT = 5 * 60

    async def post(self, request, *args, **kwargs):
        """
        Accepts POST JSON: {
            "user_id": int,
            "answer": "<str>"
        }
        Saves the answer into the Player record.
        Always returns HTTP 204 or 400 on error.
        """
        try:
            data = json.loads(request.body)
            user_id = int(data['user_id'])
            answer = str(data['answer'])
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid JSON payload')

        await save_player_answer(user_id, answer)

        return HttpResponse(status=204)

    async def get(self, request, *args, **kwargs):
        """
        Returns JSON:
        {
            "prompt": str,
            "answer0": {
                "telegram_id": int,
                "answer": str
            },
            "answer1": {
                "telegram_id": int,
                "answer": str
            }
        }
        Uses `prompt_index` from cache to pick two players.
        """
        prompt_index = await get_cached_prompt_index()
        if prompt_index is None:
            return HttpResponseBadRequest('No prompt index in cache')

        players = await fetch_two_players_by_prompt(prompt_index)
        if len(players) < 2:
            return HttpResponseBadRequest('Not enough players to form a pair')

        response_data = {
            "prompt": players[0].prompt,  # both have the same prompt by construction
            "answer0": {
                "telegram_id": players[0].telegram_id,
                "answer": players[0].answer or ""
            },
            "answer1": {
                "telegram_id": players[1].telegram_id,
                "answer": players[1].answer or ""
            },
        }

        return JsonResponse(response_data, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class VoteAPIView(View):
    """
    Async API endpoint for casting a vote.
    Expects POST JSON: {
        "voter_id": int,
        "candidate_id": int
    }
    Ensures each voter votes once, increments candidate's vote_count.
    """

    CACHE_TIMEOUT = 60

    async def post(self, request, *args, **kwargs):
        try:
            raw_body = request.body
            data = json.loads(raw_body)
            voter_id = int(data['voter_id'])
            candidate_id = int(data['candidate_id'])
        except (ValueError, KeyError, TypeError):
            return HttpResponseBadRequest('Invalid JSON payload')

        voter = await get_player_by_telegram_id(voter_id)
        if voter.is_voted:
            return HttpResponseBadRequest('Already voted')

        await mark_player_voted(voter_id)
        await increment_candidate_vote(candidate_id)

        return HttpResponse(status=204)


@method_decorator(csrf_exempt, name='dispatch')
class PromptAPIView(View):
    """
    Async endpoint for long-polling a prompt for a specific user.
    GET /api/get_prompt/?telegram_id=<ID>
    Loops until Player.prompt is non-null or until timeout.
    """

    timeout = 10 * 60  # seconds
    interval = 5  # seconds between checks

    async def get(self, request, *args, **kwargs):
        telegram_id = request.GET.get('telegram_id')
        if telegram_id is None:
            return HttpResponseBadRequest('telegram_id is required')

        try:
            telegram_id = int(telegram_id)
        except ValueError:
            return HttpResponseBadRequest('telegram_id must be an integer')

        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < self.timeout:
            player = await get_player_by_telegram_id(telegram_id)
            if player.prompt is not None:
                return JsonResponse({
                    'telegram_id': telegram_id,
                    'prompt': player.prompt.phrase
                }, status=200)

            await asyncio.sleep(self.interval)

        return HttpResponse(status=408)


@method_decorator(csrf_exempt, name='dispatch')
class PlayerCountAPIView(View):
    """
    Async endpoint that returns how many player‐pairs can be formed.
    GET /api/player_count/  --> { "count": <int> }
    """

    async def get(self, request, *args, **kwargs):
        total_count = await get_player_count()
        pairs_count = math.ceil(total_count / 2)
        return JsonResponse({'count': pairs_count}, status=200)
