from django.db import models


class Player(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=50)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


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
