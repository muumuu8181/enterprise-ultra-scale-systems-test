from django.test import TestCase
from residents.models import Household, Resident
from .models import WelfareRecipient, AssistanceRecord

class WelfareTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(address='Welfare Address')
        self.resident = Resident.objects.create(
            household=self.household,
            name_kanji='Welfare User',
            name_kana='Welfare User',
            dob='1980-01-01',
            gender='F',
            my_number='999999999999',
            status='ACTIVE'
        )

    def test_welfare_recipient(self):
        # Create WelfareRecipient
        recipient = WelfareRecipient.objects.create(
            resident=self.resident,
            is_active=True
        )

        # Verify Recipient
        self.assertIsNotNone(recipient)
        self.assertEqual(recipient.resident, self.resident)
        self.assertTrue(recipient.is_active)

        # Create AssistanceRecord
        assistance = AssistanceRecord.objects.create(
            recipient=recipient,
            assistance_type='LIVELIHOOD_PROTECTION',
            amount=150000.00,
            date_provided='2023-11-01',
            description='Monthly Support'
        )

        # Verify Assistance
        self.assertIsNotNone(assistance)
        self.assertEqual(assistance.recipient, recipient)
        self.assertEqual(float(assistance.amount), 150000.0)
        self.assertEqual(str(assistance.date_provided), '2023-11-01')
