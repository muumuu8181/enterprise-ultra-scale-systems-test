from django.db import models
from django.utils import timezone
from datetime import date

class Equipment(models.Model):
    """
    装備品基底モデル (Equipment Base Model)
    Multi-table inheritance used to allow querying all equipment.
    """
    STATUS_CHOICES = [
        ('OPERATIONAL', '稼働中'),
        ('MAINTENANCE', '整備中'),
        ('DECOMMISSIONED', '除籍'),
    ]

    name = models.CharField(max_length=100, verbose_name="名称")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="製造番号")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPERATIONAL', verbose_name="ステータス")
    assigned_unit = models.CharField(max_length=100, blank=True, verbose_name="配備部隊")
    deployment_date = models.DateField(default=date.today, verbose_name="配備日")
    classification = models.ForeignKey('core.ClearanceLevel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="機密区分")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

class Aircraft(Equipment):
    """航空機"""
    flight_hours = models.FloatField(default=0.0, verbose_name="飛行時間")
    engine_type = models.CharField(max_length=100, verbose_name="エンジン型式")

    class Meta:
        verbose_name = "航空機"
        verbose_name_plural = "航空機"

class Vessel(Equipment):
    """艦艇"""
    displacement = models.FloatField(verbose_name="排水量(トン)")
    max_speed = models.FloatField(verbose_name="最大速力(ノット)")

    class Meta:
        verbose_name = "艦艇"
        verbose_name_plural = "艦艇"

class Vehicle(Equipment):
    """車両"""
    mileage = models.FloatField(default=0.0, verbose_name="走行距離(km)")
    armor_type = models.CharField(max_length=100, verbose_name="装甲タイプ")

    class Meta:
        verbose_name = "車両"
        verbose_name_plural = "車両"

class Firearm(Equipment):
    """火器"""
    caliber = models.CharField(max_length=20, verbose_name="口径")
    rounds_fired = models.IntegerField(default=0, verbose_name="総発射弾数")

    class Meta:
        verbose_name = "火器"
        verbose_name_plural = "火器"

class DeploymentHistory(models.Model):
    """配備履歴"""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='history', verbose_name="装備品")
    previous_unit = models.CharField(max_length=100, blank=True, null=True, verbose_name="旧部隊")
    new_unit = models.CharField(max_length=100, verbose_name="新部隊")
    date = models.DateField(default=date.today, verbose_name="異動日")
    reason = models.TextField(blank=True, verbose_name="異動理由")

    def __str__(self):
        return f"{self.equipment} -> {self.new_unit} ({self.date})"
