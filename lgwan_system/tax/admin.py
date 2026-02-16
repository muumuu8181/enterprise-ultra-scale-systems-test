from django.contrib import admin
from .models import TaxPayer, TaxAssessment

admin.site.register(TaxPayer)
admin.site.register(TaxAssessment)
