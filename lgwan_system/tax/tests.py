from django.test import TestCase
from residents.models import Household, Resident
from .models import TaxPayer, TaxAssessment

class TaxTests(TestCase):
    def setUp(self):
        self.household = Household.objects.create(address='Tax Address')
        self.resident = Resident.objects.create(
            household=self.household,
            name_kanji='Tax User',
            name_kana='Tax User',
            dob='1990-01-01',
            gender='M',
            my_number='555555555555',
            status='ACTIVE'
        )

    def test_tax_calculation(self):
        # Create TaxPayer
        tax_payer = TaxPayer.objects.create(
            resident=self.resident,
            income_last_year=4430000.00
        )

        # Calculate Tax
        assessment = tax_payer.calculate_tax(year=2023)

        # Verify Assessment
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.tax_payer, tax_payer)
        self.assertEqual(assessment.year, 2023)
        self.assertEqual(assessment.status, 'PENDING')

        # Calculation: (4430000 - 430000) * 0.10 = 400000
        self.assertEqual(float(assessment.amount), 400000.0)
