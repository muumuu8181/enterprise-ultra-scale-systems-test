"""
URL configuration for defense_lms project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from logistics.views import (
    EquipmentViewSet, AircraftViewSet, VesselViewSet,
    VehicleViewSet, FirearmViewSet, UnitViewSet
)
from maintenance.views import MaintenanceRecordViewSet

router = routers.DefaultRouter()
router.register(r'units', UnitViewSet)
router.register(r'maintenance-records', MaintenanceRecordViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'aircraft', AircraftViewSet)
router.register(r'vessels', VesselViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'firearms', FirearmViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
