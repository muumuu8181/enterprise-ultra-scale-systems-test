from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'equipment', views.EquipmentViewSet)
router.register(r'aircraft', views.AircraftViewSet)
router.register(r'vessels', views.VesselViewSet)
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'firearms', views.FirearmViewSet)
router.register(r'deployment-history', views.DeploymentHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
