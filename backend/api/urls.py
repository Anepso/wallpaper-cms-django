# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WallpaperViewSet

router = DefaultRouter()
router.register(r'wallpapers', WallpaperViewSet, basename='wallpaper')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
]
