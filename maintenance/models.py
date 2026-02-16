from django.db import models
from django.conf import settings
from logistics.models import Equipment

class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='performed_maintenance')
    date = models.DateField()
    description = models.TextField()
    next_maintenance_due = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Maintenance for {self.equipment} on {self.date}"
