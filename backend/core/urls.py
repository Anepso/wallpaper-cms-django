from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home 
from . import views

urlpatterns = [
    # Root URL - Redirect berdasarkan auth status
    path('', views.home, name='home'),  # Langsung ke home view, biar login_redirect handle logic
    
    # Apps
    path('wallpapers/', include('wallpapers.urls', namespace='wallpapers')),
    path('users/', include('users.urls', namespace='users')),
    path('categories/', include('categories.urls', namespace='categories')),
    path('api/v1/', include('api.urls', namespace='api')), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Media files in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Tambahkan ini