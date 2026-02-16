from django.db import models
from residents.models import Resident

class WelfareRecipient(models.Model):
    resident = models.OneToOneField(Resident, on_delete=models.CASCADE, related_name='welfare_recipient')
    is_active = models.BooleanField(default=True)
    started_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Welfare Recipient: {self.resident.name_kanji}"

class AssistanceRecord(models.Model):
    ASSISTANCE_TYPE_CHOICES = [
        ('LIVELIHOOD_PROTECTION', 'Livelihood Protection'),
        ('DISABILITY_SUPPORT', 'Disability Support'),
        ('CHILD_ALLOWANCE', 'Child Allowance'),
        ('ELDERLY_CARE', 'Elderly Care'),
    ]

    recipient = models.ForeignKey(WelfareRecipient, on_delete=models.CASCADE, related_name='assistance_records')
    assistance_type = models.CharField(max_length=50, choices=ASSISTANCE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_provided = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.assistance_type} for {self.recipient}"
