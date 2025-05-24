from rest_framework import serializers


class RegisterPlayerInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='register_player', required=True, allow_blank=False)
    telegram_id = serializers.IntegerField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)


class SendPlayerAnswerInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='send_player_answer', required=True, allow_blank=False)
    telegram_id = serializers.IntegerField(required=True)
    answer = serializers.CharField(required=True, allow_blank=False)


class SendPlayerVoteInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='send_player_vote', required=True, allow_blank=False)
    voter_id = serializers.IntegerField(required=True)
    candidate_id = serializers.IntegerField(required=True)


class StatusOutputSerializer(serializers.Serializer):
    status = serializers.CharField()
