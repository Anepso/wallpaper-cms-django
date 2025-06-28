from django.contrib.sitemaps import Sitemap
from wallpapers.models import Wallpaper
from django.http import HttpResponse


class WallpaperSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Wallpaper.objects.filter(is_active=True)

    def location(self, obj):
        return f"/wallpapers/{obj.slug}/"
    
def robots_txt(request):
    content = "User-Agent: *\nDisallow:\nSitemap: http://127.0.0.1:8000/sitemap.xml"
    return HttpResponse(content, content_type="text/plain")
