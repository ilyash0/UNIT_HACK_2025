from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from game.models import Player


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

    async def all_answers_received(self, event):
        url = event.get('url', '/game/vote/')
        await self.send_json({
            'type': 'redirect',
            'url': url
        })
