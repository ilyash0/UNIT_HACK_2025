from json import loads, JSONDecodeError
from math import ceil

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from drf_spectacular_websocket.decorators import extend_ws_schema

from game.models import Player
from game.serializers import RegisterPlayerInputSerializer, StatusOutputSerializer, \
    SendPlayerAnswerInputSerializer, SendPlayerVoteInputSerializer, PlayersPromptsOutputSerializer, \
    PlayerAnswersOutputSerializer


@sync_to_async
def get_players(prompt_index):
    return list(Player.objects.all().order_by('prompt')[2 * (prompt_index - 1):2 * prompt_index])


@sync_to_async
def get_all_players():
    return list(Player.objects.all())


class BotConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('bot', self.channel_name)
        await self.accept()

        await self.send_json({'status': 'ok'})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('players', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if text_data is None:
            return

        try:
            content = loads(text_data)
        except JSONDecodeError:
            await self.send_json({
                'status': 'error',
                'message': 'Invalid JSON format'
            })
            return

        await self.receive_json(content)

    async def receive_json(self, content, **kwargs):
        type = content.get('type')
        if type == 'register_player':
            await self.register_player(content)
        elif type == 'send_player_answer':
            await self.send_player_answer(content)
        elif type == 'send_player_vote':
            await self.send_player_vote(content)
        elif type == 'receive_players_prompts':
            await self.receive_players_prompts(content)
        elif type == 'receive_player_answers':
            await self.receive_player_answers(content)
        else:
            await self.send_json({
                'status': 'error',
                'message': f"Unknown type '{type}'"
            })

    @extend_ws_schema(
        request=RegisterPlayerInputSerializer,
        responses={200: StatusOutputSerializer},
        type='send',
        description='Регистрация игрока'
    )
    async def register_player(self, content):
        telegram_id = content.get('telegram_id')
        username = content.get('username', '')

        if telegram_id is None:
            await self.send_json({'status': 'error', 'message': 'telegram_id is required'})
            return

        player, created = await database_sync_to_async(Player.objects.get_or_create)(
            telegram_id=telegram_id,
            defaults={'username': username, 'prompt': None, 'answer': None, 'vote_count': None},
        )

        if not created:
            player.username = username
            player.joined_at = timezone.now()
            await player.asave()

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

        return await self.send_json({'type': 'register_player', 'status': 'ok'})

    @extend_ws_schema(
        request=SendPlayerAnswerInputSerializer,
        responses={200: StatusOutputSerializer},
        type='send',
        description='Отправка ответа игрока'
    )
    async def send_player_answer(self, content):
        telegram_id = content.get('telegram_id')
        answer = content.get('answer')

        player = await Player.objects.aget(telegram_id=telegram_id)
        player.answer = answer
        await player.asave()

        total_players = await Player.objects.acount()
        answered_players = await Player.objects.filter(answer__isnull=False).acount()

        if answered_players >= total_players > 0:
            channel_layer = get_channel_layer()
            channel_layer.group_send(
                'players',
                {
                    'type': 'all_answers_received',
                }
            )

        return await self.send_json({'status': 'ok'})

    @extend_ws_schema(
        request=SendPlayerVoteInputSerializer,
        responses={200: StatusOutputSerializer},
        type='send',
        description='Отправка голоса игрока'
    )
    async def send_player_vote(self, content):
        voter_id = content.get('voter_id')
        candidate_id = content.get('candidate_id')

        voter = await Player.objects.aget(telegram_id=voter_id)
        if voter.is_voted:
            return await self.send_json({'type': 'send_player_vote', 'status': 'Already voted'})

        voter.is_voted = True
        await voter.asave()

        candidate = await Player.objects.aget(telegram_id=candidate_id)
        candidate.vote_count = (candidate.vote_count or 0) + 1
        await candidate.asave()

        channel_layer = get_channel_layer()
        await channel_layer.group_send('players', {'type': 'player_voted'})

        remaining = await Player.objects.filter(is_voted=False).acount()
        if remaining == 2:
            prompt_index = await sync_to_async(cache.get)("prompt_index") or 0

            async for p in Player.objects.filter(is_voted=True):
                p.is_voted = False
                await p.asave()

            players = await get_players(prompt_index)
            await sync_to_async(cache.set)("prompt_index", prompt_index + 1, timeout=300)

            total_players = await Player.objects.acount()
            is_all_voted = prompt_index == ceil(total_players / 2)

            result = {
                'all_voted': is_all_voted,
                "prompt": players[0].prompt.phrase,
                "player0": {
                    "username": players[0].username,
                    "answer": players[0].answer,
                    "vote_count": players[0].vote_count or 0,
                },
                "player1": {
                    "username": players[1].username,
                    "answer": players[1].answer,
                    "vote_count": players[1].vote_count or 0,
                },
            }

            await channel_layer.group_send('players', {'type': 'all_voted', 'message': result})

            if not is_all_voted:
                await channel_layer.group_send('bot', {'type': 'receive_player_answers'})

        return await self.send_json({'type': 'send_player_vote', 'status': 'ok'})

    @extend_ws_schema(
        responses={200: PlayersPromptsOutputSerializer},
        type='receive',
        description='Получение фразы игрока'
    )
    async def receive_players_prompts(self, _content):

        players = await get_all_players()

        result = []
        for p in players:
            result.append({
                'telegram_id': p.telegram_id,
                'prompt': p.prompt.phrase
            })

        return await self.send_json({'type': 'receive_players_prompts', "players": result})

    @extend_ws_schema(
        responses={200: PlayerAnswersOutputSerializer},
        type='receive',
        description='Получение ответа игрока'
    )
    async def receive_player_answers(self, _content):
        prompt_index = await sync_to_async(cache.get)('prompt_index', 0)

        players = await get_players(prompt_index)

        result = {
            "type": "receive_player_answers",
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

        return await self.send_json(result)
