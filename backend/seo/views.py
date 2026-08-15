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
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    content = f"User-Agent: *\nDisallow:\nSitemap: {sitemap_url}"
    return HttpResponse(content, content_type="text/plain")
