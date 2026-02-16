from django.db import models
from django.contrib.auth.models import AbstractUser

class ClearanceLevel(models.Model):
    """
    セキュリティクリアランスレベル
    例: UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP SECRET
    """
    name = models.CharField(max_length=50, unique=True)
    level = models.IntegerField(unique=True, help_text="数値が大きいほど機密レベルが高い")

    def __str__(self):
        return f"{self.name} ({self.level})"

    class Meta:
        ordering = ['level']

class User(AbstractUser):
    """
    拡張ユーザーモデル
    """
    clearance_level = models.ForeignKey(
        ClearanceLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="ユーザーのセキュリティクリアランス"
    )
    unit_assignment = models.CharField(max_length=100, blank=True, help_text="所属部隊")

    def __str__(self):
        return self.username
