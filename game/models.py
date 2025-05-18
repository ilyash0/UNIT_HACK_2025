from django.db import models


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


class Player(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=50)
    joined_at = models.DateTimeField(auto_now_add=True)
    prompt_id = models.ForeignKey(Prompt, on_delete=models.CASCADE, null=True)
    answer = models.TextField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    is_voted = models.BooleanField(default=False)

    def __str__(self):
        return self.username
