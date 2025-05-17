from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class PlayerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('players', self.channel_name)
        await self.accept()

        from .models import Player
        players = await database_sync_to_async(list)(
            Player.objects.order_by('joined_at').values('id', 'username', 'joined_at'))
        await self.send_json({'type': 'init', 'players': players})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('players', self.channel_name)

    async def player_joined(self, event):
        await self.send_json({'type': 'new_player', 'player': event['player']})
