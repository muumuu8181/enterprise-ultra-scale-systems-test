from django.db import models

class Household(models.Model):
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Household at {self.address}"


class Resident(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MOVED_OUT', 'Moved Out'),
        ('DECEASED', 'Deceased'),
    ]

    household = models.ForeignKey(Household, related_name='residents', on_delete=models.CASCADE)
    name_kanji = models.CharField(max_length=100)
    name_kana = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    my_number = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    move_in_date = models.DateField(auto_now_add=True)
    move_out_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name_kanji} ({self.status})"
