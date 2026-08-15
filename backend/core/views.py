from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from wallpapers.models import Wallpaper
from categories.models import Category
from taggit.models import Tag

@login_required
def home(request):
    latest_wallpapers = Wallpaper.objects.filter(is_active=True).select_related('category').prefetch_related('favorites')

    tag_slug = request.GET.get('tag', '').strip()
    active_tag = None
    if tag_slug:
        active_tag = Tag.objects.filter(slug=tag_slug).first()
        if active_tag:
            latest_wallpapers = latest_wallpapers.filter(tags__slug=tag_slug)

    latest_wallpapers = latest_wallpapers.order_by('-created_at')[:10]

    popular_categories = Category.objects.filter(wallpapers__is_active=True).annotate(
        wallpaper_count=Count('wallpapers')
    ).order_by('-wallpaper_count')[:8]

    return render(request, 'home.html', {
        'latest_wallpapers': latest_wallpapers,
        'popular_categories': popular_categories,
        'tags': Tag.objects.order_by('name'),
        'active_tag': active_tag,
    })
