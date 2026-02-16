from django.db import models

class Program(models.Model):
    """
    Represents a Series or Program concept (e.g., 'News 7').
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Episode(models.Model):
    """
    Represents a specific episode of a program.
    """
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='episodes')
    title = models.CharField(max_length=255, help_text="Episode title or date")
    episode_number = models.PositiveIntegerField(null=True, blank=True)

    # Link to the master material
    master_material = models.ForeignKey('assets.Material', on_delete=models.SET_NULL, null=True, blank=True, related_name='episodes')

    scheduled_air_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.program.title} - {self.title}"
