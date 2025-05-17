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
