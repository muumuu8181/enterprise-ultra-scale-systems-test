from django.db import models

class Case(models.Model):
    CASE_TYPES = [
        ('CIV', 'Civil'),
        ('CRM', 'Criminal'),
        ('FAM', 'Family'),
        ('ADM', 'Administrative'),
    ]
    STATUS_CHOICES = [
        ('ACT', 'Active'),
        ('CLO', 'Closed'),
        ('APP', 'Appeal'),
        ('HLD', 'On Hold'),
    ]

    case_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    case_type = models.CharField(max_length=3, choices=CASE_TYPES)
    filing_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='ACT')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.case_number}: {self.title}"

class Party(models.Model):
    PARTY_TYPES = [
        ('PLA', 'Plaintiff'),
        ('DEF', 'Defendant'),
        ('LAW', 'Lawyer'),
        ('JUD', 'Judge'),
        ('WIT', 'Witness'),
    ]

    case = models.ForeignKey(Case, related_name='parties', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    party_type = models.CharField(max_length=3, choices=PARTY_TYPES)
    contact_info = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()})"

class Hearing(models.Model):
    case = models.ForeignKey(Case, related_name='hearings', on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Hearing for {self.case.case_number} at {self.date_time}"

class Document(models.Model):
    case = models.ForeignKey(Case, related_name='documents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    doc_type = models.CharField(max_length=50)

    def __str__(self):
        return self.title

class CaseSequence(models.Model):
    year = models.IntegerField()
    case_type = models.CharField(max_length=3)
    last_serial = models.IntegerField(default=0)

    class Meta:
        unique_together = ('year', 'case_type')
