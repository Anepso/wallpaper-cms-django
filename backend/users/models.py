from django.contrib.auth.models import AbstractUser
from django.db import models
import os

def profile_image_upload_path(instance, filename):

    return os.path.join('profile_images', f'user_{instance.id}', filename)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'Regular User'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Biography'
    )

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name='Profile Picture'
    )

    def __str__(self):
        return self.username
