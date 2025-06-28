# api/serializers.py

from rest_framework import serializers
from wallpapers.models import Wallpaper

class WallpaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallpaper
        fields = '__all__'
