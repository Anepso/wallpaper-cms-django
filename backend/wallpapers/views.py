import os
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, F
from django.http import FileResponse
from django.utils import timezone
from .models import Wallpaper
from .forms import WallpaperForm
from categories.models import Category
from django.contrib.auth import get_user_model
from taggit.models import Tag
from core.decorators import is_manager, manager_required

User = get_user_model() 

class WallpaperListView(ListView):
    model = Wallpaper
    template_name = 'wallpapers/wallpaper_list.html'
    context_object_name = 'wallpapers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        search_query = self.request.GET.get('q')
        category_slug = self.request.GET.get('category')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class WallpaperAdminListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Wallpaper
    template_name = 'admin/wallpaper_admin_list.html'
    context_object_name = 'wallpapers'
    paginate_by = 10

    def test_func(self):
        return is_manager(self.request.user)

    def get_queryset(self):
        queryset = Wallpaper.objects.select_related('category', 'uploader').order_by('-created_at')

        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(uploader__username__icontains=search_query)
            )

        category_slug = self.request.GET.get('category', '').strip()
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        return context

def home(request):
    # Ambil semua wallpaper yang aktif (tanpa membatasi siapa pengunggahnya)
    latest_wallpapers = Wallpaper.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('favorites')

    # Filter berdasarkan tag jika parameter ?tag= disediakan
    tag_slug = request.GET.get('tag', '').strip()
    active_tag = None
    if tag_slug:
        active_tag = Tag.objects.filter(slug=tag_slug).first()
        if active_tag:
            latest_wallpapers = latest_wallpapers.filter(tags__slug=tag_slug)

    latest_wallpapers = latest_wallpapers.order_by('-created_at')[:10]

    # Ambil kategori populer yang memiliki wallpaper aktif
    popular_categories = Category.objects.filter(
        wallpapers__is_active=True
    ).annotate(
        wallpaper_count=Count('wallpapers')
    ).order_by('-wallpaper_count')[:10]

    return render(request, 'home.html', {
        'latest_wallpapers': latest_wallpapers,
        'popular_categories': popular_categories,
        'tags': Tag.objects.order_by('name'),
        'active_tag': active_tag,
    })

def search_wallpapers(request):
    query = request.GET.get('q', '').strip()
    orientation = request.GET.get('orientation', '').strip()
    date_range = request.GET.get('date_range', '').strip()

    wallpapers = Wallpaper.objects.filter(is_active=True).select_related('category')
    has_filter = False

    if query:
        has_filter = True
        wallpapers = wallpapers.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    if orientation in ('landscape', 'portrait', 'square'):
        has_filter = True
        wallpapers = wallpapers.filter(orientation=orientation)

    if date_range == 'terbaru':
        has_filter = True
        wallpapers = wallpapers.filter(created_at__gte=timezone.now() - timedelta(days=1))
    elif date_range == 'minggu_ini':
        has_filter = True
        wallpapers = wallpapers.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif date_range == 'bulan_ini':
        has_filter = True
        wallpapers = wallpapers.filter(created_at__gte=timezone.now() - timedelta(days=30))

    if not has_filter:
        wallpapers = Wallpaper.objects.none()

    return render(request, 'wallpapers/search_results.html', {
        'query': query,
        'wallpapers': wallpapers,
        'orientation': orientation,
        'date_range': date_range,
    })


@login_required
def toggle_favorite(request, slug):
    wallpaper = get_object_or_404(Wallpaper, slug=slug, is_active=True)

    if request.user in wallpaper.favorites.all():
        wallpaper.favorites.remove(request.user)
        messages.success(request, f'"{wallpaper.title}" dihapus dari favorit.')
    else:
        wallpaper.favorites.add(request.user)
        messages.success(request, f'"{wallpaper.title}" ditambahkan ke favorit.')

    return redirect('wallpapers:detail', slug=wallpaper.slug)


def download_wallpaper(request, slug):
    wallpaper = get_object_or_404(Wallpaper, slug=slug, is_active=True)

    # Hitung unduhan secara atomik (aman dari race condition)
    Wallpaper.objects.filter(pk=wallpaper.pk).update(downloads=F('downloads') + 1)

    filename = os.path.basename(wallpaper.image.name)
    return FileResponse(
        wallpaper.image.storage.open(wallpaper.image.name, 'rb'),
        as_attachment=True,
        filename=filename,
    )


@login_required
def favorite_wallpapers(request):
    wallpapers = request.user.favorite_wallpapers.filter(
        is_active=True
    ).select_related('category').order_by('-created_at')

    return render(request, 'wallpapers/favorites.html', {
        'wallpapers': wallpapers,
    })

def _process_upload(request):
    """Proses semua file yang diunggah (satu atau banyak sekaligus).

    Mengembalikan tuple (success_count, failed_count), atau None jika tidak
    ada file yang diunggah.
    """
    images = request.FILES.getlist('image')
    if not images:
        return None

    title_input = request.POST.get('title', '').strip()
    success_count = 0
    failed_count = 0

    for index, image in enumerate(images):
        data = request.POST.copy()
        data.setdefault('description', '')
        data.setdefault('width', '1920')
        data.setdefault('height', '1080')
        base_title = os.path.splitext(image.name)[0].replace('_', ' ').replace('-', ' ').strip() or f'Wallpaper {index + 1}'

        if len(images) == 1:
            data['title'] = title_input or base_title
        elif title_input:
            data['title'] = f'{title_input} {index + 1}'
        else:
            data['title'] = base_title

        form = WallpaperForm(data, {'image': image})
        if form.is_valid():
            wallpaper = form.save(commit=False)
            wallpaper.uploader = request.user
            wallpaper.is_active = True
            wallpaper.save()
            form.save_m2m()
            success_count += 1
        else:
            failed_count += 1

    return success_count, failed_count

@manager_required
def wallpaper_upload(request):
    if request.method == 'POST':
        result = _process_upload(request)
        if result is not None:
            success_count, failed_count = result
            if success_count:
                messages.success(request, f'{success_count} wallpaper berhasil diupload!')
            if failed_count:
                messages.error(request, f'{failed_count} wallpaper gagal diupload.')
            return redirect('wallpapers:wallpaper_admin_list')
        else:
            form = WallpaperForm(request.POST, request.FILES)
            if form.is_valid():
                wallpaper = form.save(commit=False)
                wallpaper.uploader = request.user
                wallpaper.is_active = True
                wallpaper.save()
                form.save_m2m()
                messages.success(request, 'Wallpaper berhasil diupload!')
                return redirect('wallpapers:wallpaper_admin_list')
            else:
                messages.error(request, 'Ada kesalahan dalam form. Silakan periksa kembali.')

    else:
        form = WallpaperForm()

    categories = Category.objects.all().order_by('name')

    return render(request, 'admin/upload.html', {
        'form': form,
        'categories': categories
    })

@manager_required
def add_wallpaper(request):
    categories = Category.objects.all().order_by('name')
    if request.method == 'POST':
        result = _process_upload(request)
        if result is not None:
            success_count, failed_count = result
            if success_count:
                messages.success(request, f'{success_count} wallpaper berhasil ditambahkan!')
            if failed_count:
                messages.error(request, f'{failed_count} wallpaper gagal diupload.')
            return redirect('wallpapers:wallpaper_admin_list')
        else:
            form = WallpaperForm(request.POST, request.FILES)
            if form.is_valid():
                wallpaper = form.save(commit=False)
                wallpaper.uploader = request.user
                wallpaper.is_active = True
                wallpaper.save()
                form.save_m2m()
                messages.success(request, 'Wallpaper berhasil ditambahkan!')
                return redirect('wallpapers:wallpaper_admin_list')
            else:
                messages.error(request, 'Ada kesalahan dalam form. Silakan periksa kembali.')
    else:
        form = WallpaperForm()

    return render(request, 'admin/upload.html', {
        'form': form,
        'categories': categories
    })

@login_required
def update_wallpaper(request, pk):
    wallpaper = get_object_or_404(Wallpaper, pk=pk)

    # Hanya uploader atau manajer yang boleh mengedit
    if request.user != wallpaper.uploader and not is_manager(request.user):
        messages.error(request, "Anda tidak memiliki izin untuk mengedit wallpaper ini.")
        return redirect('wallpapers:wallpaper_admin_list')

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, "Judul tidak boleh kosong.")
            return redirect('wallpapers:wallpaper_admin_list')

        # Update field secara terarah agar data lain (deskripsi, tag, dimensi,
        # is_premium, gambar) tidak tertimpa oleh data yang tidak dikirim form modal.
        wallpaper.title = title
        category_id = request.POST.get("category")
        wallpaper.category = Category.objects.filter(pk=category_id).first() if category_id else None
        wallpaper.save()
        messages.success(request, "Wallpaper berhasil diperbarui.")
    return redirect('wallpapers:wallpaper_admin_list')


def _delete_wallpaper_files(wallpaper):
    """Hapus file gambar & thumbnail wallpaper dari storage."""
    for field in (wallpaper.image, wallpaper.thumbnail):
        if field:
            try:
                field.delete(save=False)
            except Exception:
                pass


@login_required
def delete_multiple_wallpapers(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_wallpapers')

        # Filter berdasarkan permission
        wallpapers = Wallpaper.objects.filter(id__in=selected_ids)
        if not is_manager(request.user):
            wallpapers = wallpapers.filter(uploader=request.user)

        # Hapus file fisik sebelum record dihapus
        for wallpaper in wallpapers:
            _delete_wallpaper_files(wallpaper)

        count = wallpapers.count()
        wallpapers.delete()

        messages.success(request, f'{count} wallpaper berhasil dihapus!')
    return redirect('wallpapers:wallpaper_admin_list')

@login_required
def wallpaper_delete(request, pk):
    wallpaper = get_object_or_404(Wallpaper, pk=pk)

    if request.user != wallpaper.uploader and not is_manager(request.user):
        messages.error(request, "Anda tidak memiliki izin untuk menghapus wallpaper ini.")
        return redirect('wallpapers:wallpaper_admin_list')

    if request.method == 'POST':
        wallpaper_title = wallpaper.title
        _delete_wallpaper_files(wallpaper)  # Hapus file gambar & thumbnail dari storage
        wallpaper.delete()       # Hapus record dari database
        messages.success(request, f'Wallpaper "{wallpaper_title}" berhasil dihapus!')
        return redirect('wallpapers:wallpaper_admin_list')
    
    return render(request, 'admin/delete.html', {
        'object': wallpaper,
        'title': 'Hapus Wallpaper'
    })

def explore(request, slug=None):
    wallpapers = Wallpaper.objects.filter(is_active=True)
    if slug:
        wallpapers = wallpapers.filter(category__slug=slug)

    categories = Category.objects.all()
    return render(request, 'wallpapers/explore.html', {
        'wallpapers': wallpapers,
        'categories': categories,
    })

def wallpaper_detail(request, slug):
    wallpaper = get_object_or_404(Wallpaper, slug=slug, is_active=True)
    related_wallpapers = Wallpaper.objects.filter(is_active=True).select_related('category').exclude(pk=wallpaper.pk).order_by('-created_at')[:8]
    return render(request, 'wallpapers/detail.html', {
        'wallpaper': wallpaper,
        'related_wallpapers': related_wallpapers,
    })

def wallpapers_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    wallpapers = Wallpaper.objects.filter(category=category, is_active=True).order_by('-created_at')
    
    return render(request, 'wallpapers/wallpapers_by_category.html', {
        'category': category,
        'wallpapers': wallpapers,
    })

def tentang(request):
    return render(request, 'tentang.html')