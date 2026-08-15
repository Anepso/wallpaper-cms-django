# api/views.py
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, SAFE_METHODS
from wallpapers.models import Wallpaper
from .serializers import WallpaperSerializer
from core.decorators import is_manager


class IsAdminOrReadOnly(BasePermission):
    """Baca bebas untuk siapa saja; tulis hanya untuk staff/admin."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and is_manager(request.user)


class WallpaperViewSet(viewsets.ModelViewSet):
    queryset = Wallpaper.objects.all()
    serializer_class = WallpaperSerializer
    permission_classes = [IsAdminOrReadOnly]
