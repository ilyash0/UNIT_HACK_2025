from django.contrib.auth.models import User
from django.db import models


class Game(models.Model):
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    # host_user = models.ForeignKey(User, on_delete=models.CASCADE)


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
