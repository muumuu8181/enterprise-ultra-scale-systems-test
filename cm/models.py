from django.db import models

class Commercial(models.Model):
    """
    Represents a Commercial (CM) creative.
    """
    client_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    material = models.ForeignKey('assets.Material', on_delete=models.PROTECT, related_name='commercials')
    contract_id = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.client_name}] {self.title}"
