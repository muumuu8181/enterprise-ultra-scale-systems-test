from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class ClearanceLevel(models.TextChoices):
        CONFIDENTIAL = 'CONFIDENTIAL', 'Confidential'
        SECRET = 'SECRET', 'Secret'
        TOP_SECRET = 'TOP_SECRET', 'Top Secret'

    class ServiceBranch(models.TextChoices):
        ARMY = 'ARMY', 'Army'
        NAVY = 'NAVY', 'Navy'
        AIR_FORCE = 'AIR_FORCE', 'Air Force'

    clearance_level = models.CharField(
        max_length=20,
        choices=ClearanceLevel.choices,
        default=ClearanceLevel.CONFIDENTIAL,
    )
    service_branch = models.CharField(
        max_length=20,
        choices=ServiceBranch.choices,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.username} ({self.get_clearance_level_display()})"

    def get_clearance_rank(self):
        return self.get_clearance_rank_for_level(self.clearance_level)

    @classmethod
    def get_clearance_rank_for_level(cls, level):
        ranks = {
            cls.ClearanceLevel.CONFIDENTIAL: 1,
            cls.ClearanceLevel.SECRET: 2,
            cls.ClearanceLevel.TOP_SECRET: 3,
        }
        return ranks.get(level, 0)
