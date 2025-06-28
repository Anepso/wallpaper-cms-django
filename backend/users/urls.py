from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'users'

urlpatterns = [
    # Home Page
    path('', views.home, name='home'),

    # Login & Logout
    path('login/', views.custom_login, name='login'),
    
    path('login/redirect/', views.login_redirect, name='login_redirect'),
    
    path('logout/', 
         LogoutView.as_view(
             next_page=reverse_lazy('users:login')),
         name='logout'),

    # Registration & Profile
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Password Reset
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             success_url=reverse_lazy('users:password_reset_done')),
         name='password_reset'),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')),
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    # Dashboard (Admin-only)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin User Management
    path('admin/users/', views.user_list, name='user-list'),
    path('admin/users/add/', views.user_add, name='user-add'),
    path('admin/users/banned/', views.user_banned, name='user-banned'),
    path('admin/users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle-user-status'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
