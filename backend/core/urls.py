from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # SEO - Harus didaftarkan sebelum root URL agar sitemap.xml & robots.txt bisa diakses
    path('', include('seo.urls')),

    # Root URL - Redirect berdasarkan auth status
    path('', views.home, name='home'),  # Langsung ke home view, biar login_redirect handle logic
    
    # Apps
    path('wallpapers/', include('wallpapers.urls', namespace='wallpapers')),
    path('users/', include('users.urls', namespace='users')),
    path('categories/', include('categories.urls', namespace='categories')),
    path('api/v1/', include('api.urls', namespace='api')), 
]

# Media files in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Tambahkan ini