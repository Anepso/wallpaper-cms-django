from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib import messages
from .models import Category
from .forms import CategoryForm
from wallpapers.models import Wallpaper
from django.db import connection

class CategoryListView(ListView):
    model = Category
    template_name = 'categories/list.html'  # Changed to match your structure
    context_object_name = 'categories'
    paginate_by = 12
    ordering = ['name']

def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Kategori "{category.name}" berhasil ditambahkan!')
            return redirect('categories:list')
    else:
        form = CategoryForm()
    
    return render(request, 'categories/add_category.html', {
        'form': form,
        'title': 'Tambah Kategori Baru'
    })

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    wallpapers = Wallpaper.objects.filter(category=category).order_by('-created_at')
    
    return render(request, 'categories/detail.html', {
        'category': category,
        'wallpapers': wallpapers,
        'title': f'Kategori {category.name}'
    })

def edit_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Kategori "{category.name}" berhasil diperbarui!')
            return redirect('categories:detail', slug=category.slug)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'categories/add.html', {
        'form': form,
        'title': 'Edit Kategori',
        'edit_mode': True
    })

def delete_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        try:
            # Cek apakah tabel wallpapers_wallpaper ada
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('wallpapers_wallpaper')")
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    Wallpaper.objects.filter(category=category).update(category=None)
            
            category.delete()
            messages.success(request, 'Kategori berhasil dihapus!')
            return redirect('categories:list')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('categories:detail', slug=slug)
    
    return render(request, 'categories/delete_confirm.html', {'category': category})