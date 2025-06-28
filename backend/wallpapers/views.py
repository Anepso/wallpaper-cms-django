from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Wallpaper
from .forms import WallpaperForm
from categories.models import Category
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Q, Count

User = get_user_model() 

class WallpaperListView(ListView):
    model = Wallpaper
    template_name = 'wallpapers/list.html'
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
        return self.request.user.is_staff or getattr(self.request.user, 'role', None) == 'admin'

    def get_queryset(self):
        return Wallpaper.objects.all().order_by('-created_at')

def home(request):
    # Ambil semua wallpaper yang aktif (tanpa membatasi siapa pengunggahnya)
    latest_wallpapers = Wallpaper.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10]

    # Ambil kategori populer yang memiliki wallpaper
    popular_categories = Category.objects.annotate(
        wallpaper_count=Count('wallpapers')
    ).filter(wallpaper_count__gt=0).order_by('-wallpaper_count')[:10]

    return render(request, 'home.html', {
        'latest_wallpapers': latest_wallpapers,
        'popular_categories': popular_categories,
    })

def search_wallpapers(request):
    query = request.GET.get('q')
    wallpapers = Wallpaper.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) | 
        Q(tags__name__icontains=query),
        is_active=True
    ).distinct()
    
    return render(request, 'wallpapers/search_results.html', {
        'query': query,
        'wallpapers': wallpapers,
    })

@login_required
def wallpaper_upload(request):
    if request.method == 'POST':
        form = WallpaperForm(request.POST, request.FILES)
        if form.is_valid():
            wallpaper = form.save(commit=False)
            wallpaper.uploader = request.user
            wallpaper.is_active = True  # PENTING
            wallpaper.save()
            form.save_m2m()
            print(f"[DEBUG] Wallpaper disimpan: {wallpaper.title}, is_active={wallpaper.is_active}")
            messages.success(request, 'Wallpaper berhasil diupload!')
            return redirect('wallpapers:admin_list')
        else:
            print('[DEBUG] request.FILES:', request.FILES)

    else:
        form = WallpaperForm()

    categories = Category.objects.all().order_by('name')

    return render(request, 'admin/upload.html', {
        'form': form,
        'categories': categories
    })

@login_required
def add_wallpaper(request):
    categories = Category.objects.all().order_by('name')
    if request.method == 'POST':
        form = WallpaperForm(request.POST, request.FILES)
        if form.is_valid():
            wallpaper = form.save(commit=False)
            wallpaper.uploader = request.user
            wallpaper.is_active = True
            wallpaper.save()
            form.save_m2m()
            messages.success(request, 'Wallpaper berhasil ditambahkan!')
            return redirect('wallpapers:admin_list')  # Pastikan URL ini ada dan mengarah ke WallpaperListView
        else:
            messages.error(request, 'Ada kesalahan dalam form. Silakan periksa kembali.')
    else:
        form = WallpaperForm()

    return render(request, 'admin/add.html', {
        'form': form,
        'categories': categories
    })

@login_required
def update_wallpaper(request):
    if request.method == "POST":
        wallpaper_id = request.POST.get("wallpaper_id")
        wallpaper = get_object_or_404(Wallpaper, id=wallpaper_id)

        # Cek apakah user adalah uploader atau admin
        if request.user != wallpaper.uploader and not request.user.is_staff:
            messages.error(request, "Anda tidak memiliki izin untuk mengedit wallpaper ini.")
            return redirect('wallpapers:wallpaper_admin_list')

        form = WallpaperForm(request.POST, request.FILES, instance=wallpaper)
        if form.is_valid():
            form.save()
            messages.success(request, "Wallpaper berhasil diperbarui.")
        else:
            messages.error(request, "Gagal memperbarui wallpaper. Pastikan data valid.")
    return redirect('wallpapers:wallpaper_admin_list') 

@login_required
def delete_multiple_wallpapers(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_wallpapers')
        
        # Filter berdasarkan permission
        wallpapers = Wallpaper.objects.filter(id__in=selected_ids)
        if not request.user.is_staff and request.user.role != 'admin':
            wallpapers = wallpapers.filter(uploader=request.user)
            
        count = wallpapers.count()
        wallpapers.delete()
        
        messages.success(request, f'{count} wallpaper berhasil dihapus!')
    return redirect('wallpapers:admin_list')

@login_required
def wallpaper_delete(request, pk):
    wallpaper = get_object_or_404(Wallpaper, pk=pk)
    
    if request.method == 'POST':
        wallpaper_title = wallpaper.title
        wallpaper.image.delete()  # Hapus file gambar dari storage
        wallpaper.delete()       # Hapus record dari database
        messages.success(request, f'Wallpaper "{wallpaper_title}" berhasil dihapus!')
        return redirect('admin:list')
    
    return render(request, 'admin/delete_confirm.html', {
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
    wallpaper = get_object_or_404(Wallpaper, slug=slug)
    return render(request, 'wallpapers/detail.html', {'wallpaper': wallpaper})

def wallpapers_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    wallpapers = Wallpaper.objects.filter(category=category, is_active=True).order_by('-created_at')
    
    return render(request, 'wallpapers/wallpapers_by_category.html', {
        'category': category,
        'wallpapers': wallpapers,
    })

def tentang(request):
    return render(request, 'tentang.html')