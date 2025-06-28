from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from wallpapers.models import Wallpaper
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    total_wallpapers = Wallpaper.objects.count()
    total_users = get_user_model().objects.count()
    return render(request, 'admin/dashboard.html', {
        'total_wallpapers': total_wallpapers,
        'total_users': total_users,
    })

@login_required
def home(request):
    latest_wallpapers = Wallpaper.objects.order_by('-created_at')[:10]
    return render(request, 'home.html', {
        'latest_wallpapers': latest_wallpapers
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}!')
            login(request, user)  # Auto login after registration
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})