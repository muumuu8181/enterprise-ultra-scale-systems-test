from django.db import models
from residents.models import Resident

class TaxPayer(models.Model):
    resident = models.OneToOneField(Resident, on_delete=models.CASCADE, related_name='tax_payer')
    income_last_year = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"TaxPayer: {self.resident.name_kanji}"

    def calculate_tax(self, year):
        """
        Simple tax calculation:
        - Basic deduction: 430,000
        - Tax rate: 10%
        """
        income = float(self.income_last_year)
        deduction = 430000
        taxable_income = max(0, income - deduction)
        tax_amount = taxable_income * 0.10

        assessment, created = TaxAssessment.objects.update_or_create(
            tax_payer=self,
            year=year,
            defaults={'amount': tax_amount, 'status': 'PENDING'}
        )
        return assessment

class TaxAssessment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    tax_payer = models.ForeignKey(TaxPayer, on_delete=models.CASCADE, related_name='assessments')
    year = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tax Assessment {self.year} for {self.tax_payer}"
