from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import User, ClearanceLevel
from logistics.models import Aircraft

class EquipmentTests(APITestCase):
    def setUp(self):
        # Setup clearance
        self.clearance = ClearanceLevel.objects.create(name="SECRET", level=5)

        # Setup user
        self.user = User.objects.create_user(
            username='officer',
            password='password123',
            clearance_level=self.clearance
        )
        self.client.force_authenticate(user=self.user)

    def test_create_aircraft(self):
        """
        航空機の新規登録テスト
        """
        url = reverse('aircraft-list')
        data = {
            "name": "F-35A",
            "serial_number": "79-8705",
            "status": "OPERATIONAL",
            "assigned_unit": "302SQ",
            "flight_hours": 120.5,
            "engine_type": "F135-PW-100"
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Aircraft.objects.count(), 1)
        self.assertEqual(Aircraft.objects.get().name, "F-35A")

    def test_deployment_history(self):
        """
        配備履歴の記録テスト
        """
        # Create Aircraft
        aircraft = Aircraft.objects.create(
            name="F-15J",
            serial_number="42-8832",
            assigned_unit="201SQ",
            flight_hours=2000.0,
            engine_type="F100-IHI-220E"
        )

        url = reverse('deploymenthistory-list')
        data = {
            "equipment": aircraft.id,
            "previous_unit": "201SQ",
            "new_unit": "303SQ",
            "date": "2023-10-01",
            "reason": "Rotation"
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(aircraft.history.count(), 1)
        self.assertEqual(aircraft.history.first().new_unit, "303SQ")
