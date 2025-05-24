from rest_framework import serializers


class RegisterPlayerInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='register_player')
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False, allow_blank=True)


class RegisterPlayerOutputSerializer(serializers.Serializer):
    status = serializers.CharField()
