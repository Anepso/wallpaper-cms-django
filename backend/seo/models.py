from django.db import models

class SEOSettings(models.Model):
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    
    class Meta:
        verbose_name = "SEO Setting"
        verbose_name_plural = "SEO Settings"