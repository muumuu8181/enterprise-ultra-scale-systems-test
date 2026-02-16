from rest_framework import viewsets, permissions
from .models import MaintenanceRecord
from .serializers import MaintenanceRecordSerializer
from core.models import User

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

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

        return queryset.filter(equipment__required_clearance__in=allowed_levels)
