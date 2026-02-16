from rest_framework import viewsets, permissions
from core.permissions import HasClearance
from .models import Equipment, Aircraft, Vessel, Vehicle, Firearm, Unit
from .serializers import (
    EquipmentSerializer, AircraftSerializer, VesselSerializer,
    VehicleSerializer, FirearmSerializer, UnitSerializer
)
from core.models import User

class BaseClearanceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasClearance]

    def get_queryset(self):
        # Allow schema generation to work without a request
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset

        user_rank = user.get_clearance_rank()

        allowed_levels = [
            choice[0] for choice in User.ClearanceLevel.choices
            if User.get_clearance_rank_for_level(choice[0]) <= user_rank
        ]

        return queryset.filter(required_clearance__in=allowed_levels)

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]

class EquipmentViewSet(BaseClearanceViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer

class AircraftViewSet(BaseClearanceViewSet):
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer

class VesselViewSet(BaseClearanceViewSet):
    queryset = Vessel.objects.all()
    serializer_class = VesselSerializer

class VehicleViewSet(BaseClearanceViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class FirearmViewSet(BaseClearanceViewSet):
    queryset = Firearm.objects.all()
    serializer_class = FirearmSerializer
