from rest_framework import viewsets, permissions
from .models import Equipment, Aircraft, Vessel, Vehicle, Firearm, DeploymentHistory
from .serializers import (
    EquipmentSerializer, AircraftSerializer, VesselSerializer,
    VehicleSerializer, FirearmSerializer, DeploymentHistorySerializer
)

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class AircraftViewSet(viewsets.ModelViewSet):
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer
    permission_classes = [permissions.IsAuthenticated]

class VesselViewSet(viewsets.ModelViewSet):
    queryset = Vessel.objects.all()
    serializer_class = VesselSerializer
    permission_classes = [permissions.IsAuthenticated]

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

class FirearmViewSet(viewsets.ModelViewSet):
    queryset = Firearm.objects.all()
    serializer_class = FirearmSerializer
    permission_classes = [permissions.IsAuthenticated]

class DeploymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = DeploymentHistory.objects.all()
    serializer_class = DeploymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
