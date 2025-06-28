# core/models.py
from django.db import models

class CMSModule(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20)
    installed_date = models.DateTimeField(auto_now_add=True)
    settings = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.name} v{self.version}"