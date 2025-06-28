from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='list'),  # Halaman daftar kategori
    path('add/', views.add_category, name='add'),             # Form tambah kategori
    path('<slug:slug>/', views.category_detail, name='detail'),
    path('<slug:slug>/edit/', views.edit_category, name='edit'),
    path('<slug:slug>/delete/', views.delete_category, name='delete'),
]
