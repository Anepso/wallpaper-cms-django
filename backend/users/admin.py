from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserChangeForm
from django.contrib.auth.forms import UserCreationForm

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = UserCreationForm
    model = CustomUser
    list_display = ['username', 'email', 'is_staff']

admin.site.register(CustomUser, CustomUserAdmin)