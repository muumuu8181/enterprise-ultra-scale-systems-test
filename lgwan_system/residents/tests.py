from django.test import TestCase, Client
from django.urls import reverse
from .models import Household, Resident
import json
import hashlib
from datetime import date

class ResidentsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_headers = {'HTTP_AUTHORIZATION': 'Bearer secret-token-123'}

    def test_move_in(self):
        url = reverse('move_in')
        data = {
            'address': '1-2-3 Chiyoda, Tokyo',
            'residents': [
                {
                    'name_kanji': 'Test Taro',
                    'name_kana': 'Test Taro',
                    'dob': '1990-01-01',
                    'gender': 'M',
                    'my_number': '123456789012'
                }
            ]
        }
        # Add Authorization header
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)

        household = Household.objects.first()
        self.assertIsNotNone(household)
        self.assertEqual(household.address, '1-2-3 Chiyoda, Tokyo')

        resident = Resident.objects.first()
        self.assertIsNotNone(resident)
        self.assertEqual(resident.name_kanji, 'Test Taro')
        self.assertEqual(resident.status, 'ACTIVE')
        self.assertEqual(resident.household, household)

        # Verify My Number is hashed
        expected_hash = hashlib.sha256('123456789012'.encode()).hexdigest()
        self.assertEqual(resident.my_number, expected_hash)

    def test_move_out(self):
        household = Household.objects.create(address='Existing Address')
        resident = Resident.objects.create(
            household=household,
            name_kanji='Moving User',
            name_kana='Moving User',
            dob='1980-01-01',
            gender='F',
            my_number='hash_of_987654321098', # Simulate already hashed or just stored
            status='ACTIVE'
        )

        url = reverse('move_out')
        data = {
            'resident_id': resident.id,
            'move_out_date': '2023-10-27'
        }
        response = self.client.post(
            url,
            json.dumps(data),
            content_type='application/json',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)

        resident.refresh_from_db()
        self.assertEqual(resident.status, 'MOVED_OUT')
        self.assertEqual(str(resident.move_out_date), '2023-10-27')

    def test_certificate(self):
        household = Household.objects.create(address='Cert Address')
        resident = Resident.objects.create(
            household=household,
            name_kanji='Cert User',
            name_kana='Cert User',
            dob='2000-01-01',
            gender='M',
            my_number='hash_of_111222333444',
            status='ACTIVE'
        )

        url = reverse('certificate', args=[resident.id])
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['certificate_type'], 'Juminhyo')
        self.assertEqual(data['resident']['name_kanji'], 'Cert User')

    def test_unauthorized(self):
        url = reverse('move_in')
        response = self.client.post(url, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 401)
