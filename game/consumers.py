from json import dumps

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

    async def player_joined(self, event):
        await self.send_json({'type': 'new_player', 'player': event['player']})

    async def all_voted(self, event):
        message = event['message']
        await self.send(text_data=dumps(message))

    async def all_answers_received(self, event):
        url = event.get('url', '/game/vote/')
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

    async def receive_json(self, content, **kwargs):
        action = content.get('type')
        if action == 'register_player':
            await self.register_player(content)
        else:
            await self.send_json({
                'status': 'error',
                'message': f"Unknown action '{action}'"
            })

    @extend_ws_schema(
        request=RegisterPlayerInputSerializer,
        responses={200: RegisterPlayerOutputSerializer},
        type='send',
        description='Регистрация игрока через WebSocket'
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
            await database_sync_to_async(player.save)()

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
