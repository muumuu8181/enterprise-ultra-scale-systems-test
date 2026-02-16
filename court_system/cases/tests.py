from django.test import TestCase, Client
from django.urls import reverse
from .models import Case, Party
from .utils import generate_case_number
import datetime

class CaseModelTest(TestCase):
    def test_case_creation(self):
        case = Case.objects.create(
            case_number="2024-CIV-0001",
            title="Test Case",
            case_type="CIV",
            description="A test case"
        )
        self.assertEqual(case.title, "Test Case")
        self.assertEqual(str(case), "2024-CIV-0001: Test Case")

class PartyModelTest(TestCase):
    def setUp(self):
        self.case = Case.objects.create(
            case_number="2024-CIV-0001",
            title="Test Case",
            case_type="CIV"
        )

    def test_party_creation(self):
        party = Party.objects.create(
            case=self.case,
            name="John Doe",
            party_type="PLA",
            contact_info="123 Main St"
        )
        self.assertEqual(party.name, "John Doe")
        self.assertEqual(party.case, self.case)
        self.assertIn("Plaintiff", str(party))

class UtilsTest(TestCase):
    def test_generate_case_number(self):
        year = datetime.date.today().year

        # Test first case
        case_num1 = generate_case_number("CIV")
        self.assertEqual(case_num1, f"{year}-CIV-0001")

        # Create a case with this number
        Case.objects.create(case_number=case_num1, title="Case 1", case_type="CIV")

        # Test second case
        case_num2 = generate_case_number("CIV")
        self.assertEqual(case_num2, f"{year}-CIV-0002")

class CaseViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_case_view(self):
        url = reverse('case_create')
        data = {
            'title': 'New View Case',
            'case_type': 'CRM',
            'description': 'Created via view'
        }
        response = self.client.post(url, data)

        # Should redirect after success
        self.assertEqual(response.status_code, 302)

        # Verify case exists
        case = Case.objects.get(title='New View Case')
        year = datetime.date.today().year
        self.assertTrue(case.case_number.startswith(f"{year}-CRM-"))
        self.assertEqual(case.description, 'Created via view')

    def test_case_list_view(self):
        Case.objects.create(case_number="2024-CIV-0001", title="List Case", case_type="CIV")
        url = reverse('case_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "List Case")

    def test_case_detail_view(self):
        case = Case.objects.create(case_number="2024-CIV-0001", title="Detail Case", case_type="CIV")
        url = reverse('case_detail', args=[case.case_number])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Case")
