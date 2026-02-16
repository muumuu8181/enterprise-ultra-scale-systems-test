from django.db import models
from core.models import User

class Unit(models.Model):
    name = models.CharField(max_length=100)
    base_location = models.CharField(max_length=100)
    commanding_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='commanded_units')

    def __str__(self):
        return self.name

class Equipment(models.Model):
    class Status(models.TextChoices):
        OPERATIONAL = 'OPERATIONAL', 'Operational'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        DECOMMISSIONED = 'DECOMMISSIONED', 'Decommissioned'

    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPERATIONAL)
    acquisition_date = models.DateField()
    required_clearance = models.CharField(
        max_length=20,
        choices=User.ClearanceLevel.choices,
        default=User.ClearanceLevel.CONFIDENTIAL
    )
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment')

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

class Aircraft(Equipment):
    flight_hours = models.IntegerField(default=0)
    max_altitude = models.IntegerField(help_text="In feet")

class Vessel(Equipment):
    displacement = models.IntegerField(help_text="In tons")
    max_speed = models.IntegerField(help_text="In knots")

class Vehicle(Equipment):
    mileage = models.IntegerField(default=0)
    transmission_type = models.CharField(max_length=20)

class Firearm(Equipment):
    caliber = models.CharField(max_length=20)
    rate_of_fire = models.IntegerField(help_text="Rounds per minute")
