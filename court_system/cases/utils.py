import datetime
from django.db import transaction
from .models import CaseSequence

def generate_case_number(case_type):
    """
    Generates a unique case number in the format YYYY-TYPE-SERIAL.
    e.g., 2024-CIV-0001
    Uses CaseSequence model to ensure thread-safety.
    """
    year = datetime.date.today().year

    with transaction.atomic():
        # Lock the sequence row or create it safely
        sequence, created = CaseSequence.objects.select_for_update().get_or_create(
            year=year,
            case_type=case_type,
            defaults={'last_serial': 0}
        )

        sequence.last_serial += 1
        sequence.save()

    return f"{year}-{case_type}-{sequence.last_serial:04d}"
