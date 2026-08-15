from django.urls import path
from django.contrib.sitemaps.views import sitemap
from .views import WallpaperSitemap
from .views import robots_txt

sitemaps = {
    'wallpapers': WallpaperSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path("robots.txt", robots_txt, name="robots_txt"),
]
