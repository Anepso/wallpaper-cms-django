from django.urls import path
from . import views
from .views import WallpaperListView, WallpaperAdminListView, add_wallpaper, wallpaper_upload, update_wallpaper

app_name = 'wallpapers'

urlpatterns = [
    path('', views.home, name='home'),  
    path('search/', views.search_wallpapers, name='search'),

    path('explore/', views.explore, name='explore'),
    
    path('tentang/', views.tentang, name='tentang'),

    path('list/', WallpaperListView.as_view(), name='list'),

    path('admin/wallpaper_list/', WallpaperAdminListView.as_view(), name='wallpaper_admin_list'),
    path('admin/add/', add_wallpaper, name='add'),
    path('admin/upload/', wallpaper_upload, name='upload'),
    path('wallpapers/edit/<int:pk>/', views.update_wallpaper, name='edit'),
    path('category/<slug:slug>/', views.wallpapers_by_category, name='category'),
    
    path('delete/<int:pk>/', views.wallpaper_delete, name='delete'),
    path('delete-multiple/', views.delete_multiple_wallpapers, name='delete_multiple'),

    
    path('<slug:slug>/', views.wallpaper_detail, name='detail'),
]

