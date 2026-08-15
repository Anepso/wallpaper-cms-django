from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from wallpapers.models import Wallpaper

@login_required
def home(request):
    latest_wallpapers = Wallpaper.objects.filter(is_active=True).order_by('-created_at')[:10]
    return render(request, 'home.html', {
        'latest_wallpapers': latest_wallpapers
    })
