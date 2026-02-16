from rest_framework import serializers
from .models import MaintenanceRecord
from core.models import User

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'

    def validate_equipment(self, value):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            # If request is missing (e.g. testing) or user not authenticated, rely on permission classes.
            return value

        user = request.user
        if user.is_superuser:
            return value

        user_rank = user.get_clearance_rank()
        eq_rank = User.get_clearance_rank_for_level(value.required_clearance)

        if user_rank < eq_rank:
            raise serializers.ValidationError("Insufficient clearance for this equipment.")

        return value
