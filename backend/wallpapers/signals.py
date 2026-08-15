from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Wallpaper  # Ganti dengan model Anda

@receiver(post_save, sender=Wallpaper)
def handle_wallpaper_save(sender, instance, created, **kwargs):
    """Signal handler untuk wallpaper save"""
    if created:
        print(f"Wallpaper baru dibuat: {instance.title}")
    # Tambahkan logika custom di sini