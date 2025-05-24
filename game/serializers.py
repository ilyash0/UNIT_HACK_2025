from rest_framework import serializers


class RegisterPlayerInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='register_player', allow_blank=False)
    telegram_id = serializers.IntegerField(required=True)
    username = serializers.CharField(required=False, allow_blank=True)


class SendPlayerAnswerInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='send_player_answer', allow_blank=False)
    telegram_id = serializers.IntegerField(required=True)
    answer = serializers.CharField(required=True, allow_blank=False)


class SendPlayerVoteInputSerializer(serializers.Serializer):
    type = serializers.CharField(default='send_player_vote', allow_blank=False)
    voter_id = serializers.IntegerField(required=True)
    candidate_id = serializers.IntegerField(required=True)


class StatusOutputSerializer(serializers.Serializer):
    status = serializers.CharField()


class PlayerPromptOutputSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    prompt = serializers.CharField()


class PlayerAnswersOutputSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    answer0 = serializers.DictField(
        telegram_id=serializers.IntegerField(),
        answer=serializers.CharField()
    )
    answer1 = serializers.DictField(
        telegram_id=serializers.IntegerField(),
        answer=serializers.CharField()
    )
