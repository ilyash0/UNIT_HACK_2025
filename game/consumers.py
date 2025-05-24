from json import dumps, loads, JSONDecodeError

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone
from drf_spectacular_websocket.decorators import extend_ws_schema

from game.models import Player
from game.serializers import RegisterPlayerInputSerializer, RegisterPlayerOutputSerializer


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('players', self.channel_name)
        await self.accept()

        players = await database_sync_to_async(list)(
            Player.objects.order_by('joined_at').values('id', 'username'))
        await self.send_json({'type': 'init', 'players': players})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('players', self.channel_name)

    async def player_joined(self, content):
        await self.send_json({'type': 'new_player', 'player': content['player']})

    async def all_voted(self, content):
        message = content['message']
        await self.send(text_data=dumps(message))

    async def all_answers_received(self, content):
        url = content.get('url', '/game/vote/')
        await self.send_json({
            'type': 'redirect',
            'url': url
        })


class BotConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('bot', self.channel_name)
        await self.accept()

        await self.send_json({'status': 'ok'})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('players', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if not text_data:
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
        else:
            await self.send_json({
                'status': 'error',
                'message': f"Unknown type '{type}'"
            })

    @extend_ws_schema(
        request=RegisterPlayerInputSerializer,
        responses={200: RegisterPlayerOutputSerializer},
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

        await self.send_json({'status': 'ok'})

    @extend_ws_schema(
        request=RegisterPlayerInputSerializer,
        responses={200: RegisterPlayerOutputSerializer},
        type='send',
        description='Регистрация игрока'
    )
    async def send_player_answer(self, content):
        telegram_id = content.get('telegram_id')
        answer = content.get('answer')

        player = await Player.objects.aget(telegram_id=telegram_id)
        player.answer = answer
        await player.asave()

        total_players = Player.objects.count()
        answered_players = Player.objects.filter(answer__isnull=False).count()

        if answered_players >= total_players > 0:
            channel_layer = get_channel_layer()
            channel_layer.group_send(
                'players',
                {
                    'type': 'all_answers_received',
                }
            )

        await self.send_json({'status': 'ok'})
