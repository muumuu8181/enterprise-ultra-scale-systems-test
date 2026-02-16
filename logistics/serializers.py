from rest_framework import serializers
from .models import Equipment, Aircraft, Vessel, Vehicle, Firearm, DeploymentHistory

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'

class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = '__all__'

class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class FirearmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firearm
        fields = '__all__'

class DeploymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentHistory
        fields = '__all__'
