# wallpapers/admin.py
from django.contrib import admin
from .models import Wallpaper
from categories.models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Wallpaper)
class WallpaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    list_filter = ('category',)