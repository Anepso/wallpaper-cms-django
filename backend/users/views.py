from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from wallpapers.models import Wallpaper
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from core.decorators import manager_required

User = get_user_model()

def login_redirect(request):
    """Redirect berdasarkan role user."""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    # Admin ke dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('users:dashboard')
    
    # User biasa ke home 
    return redirect('wallpapers:home')

@manager_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.user == user:
        messages.warning(request, "Anda tidak dapat mengubah status akun Anda sendiri.")
        return redirect('users:user-list')

    user.is_active = not user.is_active
    user.save()

    status = "diaktifkan" if user.is_active else "dibanned"
    messages.success(request, f"Akun {user.username} berhasil {status}.")
    return redirect('users:user-list')

@manager_required
def dashboard(request):
    context = {
        'total_wallpapers': Wallpaper.objects.count(),
        'total_users': User.objects.count()
    }
    return render(request, 'admin/dashboard.html', context)

def register(request):
    if request.user.is_authenticated:
        return login_redirect(request)
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return login_redirect(request)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect(reverse_lazy('users:profile'))
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

import logging
logger = logging.getLogger(__name__)

def custom_login(request):
    if request.user.is_authenticated:
        logger.info(f"{request.user.username} is already authenticated")
        return login_redirect(request)
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"{user.username} logged in, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
            messages.success(request, f'Welcome back, {user.username}!')
            return login_redirect(request)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

# Daftar semua pengguna (khusus staf/admin)
@staff_member_required
def user_list(request):
    users = User.objects.all()
    return render(request, 'users/user_list.html', {'users': users})

# Tambah pengguna
@staff_member_required
def user_add(request):
    return render(request, 'users/user_add.html')

# Daftar pengguna yang diblokir
@staff_member_required
def user_banned(request):
    banned_users = User.objects.filter(is_active=False)
    return render(request, 'users/user_banned.html', {'banned_users': banned_users})