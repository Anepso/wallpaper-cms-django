from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib import messages
from .models import Category
from .forms import CategoryForm
from wallpapers.models import Wallpaper
from core.decorators import manager_required

class CategoryListView(ListView):
    model = Category
    template_name = 'categories/list.html'  # Changed to match your structure
    context_object_name = 'categories'
    paginate_by = 12
    ordering = ['name']

@manager_required
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
    
    return render(request, 'categories/category_detail.html', {
        'category': category,
        'wallpapers': wallpapers,
        'title': f'Kategori {category.name}'
    })

@manager_required
def edit_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            old_thumbnail = category.thumbnail
            category = form.save()
            # Hapus file thumbnail lama jika diganti dengan yang baru
            new_thumbnail = form.cleaned_data.get('thumbnail')
            if new_thumbnail and old_thumbnail and old_thumbnail.name != category.thumbnail.name:
                try:
                    old_thumbnail.delete(save=False)
                except Exception:
                    pass
            messages.success(request, f'Kategori "{category.name}" berhasil diperbarui!')
            return redirect('categories:detail', slug=category.slug)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'categories/add_category.html', {
        'form': form,
        'title': 'Edit Kategori',
        'edit_mode': True
    })

@manager_required
def delete_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    if request.method == 'POST':
        category_name = category.name
        # Lepaskan relasi wallpaper ke kategori ini
        Wallpaper.objects.filter(category=category).update(category=None)
        # Hapus file thumbnail dari storage jika ada
        if category.thumbnail:
            try:
                category.thumbnail.delete(save=False)
            except Exception:
                pass
        category.delete()
        messages.success(request, f'Kategori "{category_name}" berhasil dihapus!')
        return redirect('categories:list')
    
    return render(request, 'categories/delete_confirm.html', {'category': category})