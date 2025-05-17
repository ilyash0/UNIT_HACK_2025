from django.db import models


class Game(models.Model):
    code = models.CharField(max_length=5, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default=False)

    def all_ready(self):
        players = self.players.all()
        return players.exists() and all(p.ready for p in players)

    def __str__(self):
        return f"{self.code} ({'Started' if self.started else 'Waiting'})"


class Player(models.Model):
    game = models.ForeignKey(Game, related_name='players', on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50)
    joined_at = models.DateTimeField(auto_now_add=True)
    ready = models.BooleanField(default=False)
    is_host = models.BooleanField(default=False)

    class Meta:
        unique_together = ('game', 'nickname')

    def __str__(self):
        return f"{self.nickname} ({'Ready' if self.ready else 'Not ready'})"


class Prompt(models.Model):
    phrase = models.TextField()

    def __str__(self):
        return self.phrase


class BackupAnswer(models.Model):
    text = models.TextField()
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name_plural = 'Backup Answers'
        verbose_name = 'Backup Answer'
        db_table = 'backup_answers'
